# -*- coding: utf-8 -*-
"""collective.exportimport import-side customizations.

Registered (zcml:condition="installed collective.exportimport") as
@@import_content on the PloneMeeting browser layer, overriding the
stock view. All AT camelCase -> DX snake_case transforms happen here,
at import time — the exported JSON stays faithful to the Plone 4.3
source (see MIGRATION_DATA.md at the buildout root).
"""

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from collective.exportimport.import_content import ImportContent
from collective.iconifiedcategory.behaviors.iconifiedcategorization import \
    IIconifiedCategorizationMarker
from collective.iconifiedcategory.content.category import ICategory
from collective.iconifiedcategory.content.events import _cookCssResources
from collective.iconifiedcategory.content.subcategory import ISubcategory
from collective.iconifiedcategory.utils import update_all_categorized_elements
from persistent.mapping import PersistentMapping
from plone import api
from plone.app.textfield.interfaces import IRichText
from plone.dexterity.utils import iterSchemata
from plone.registry.interfaces import IRegistry
from plone.restapi.interfaces import IDeserializeFromJson
from plonemeeting.core.config import ROOT_FOLDER
from plonemeeting.core.config import TOOL_ID
from plonemeeting.core.content.meetingconfig import IMeetingConfig
from plonemeeting.core.interfaces import IMeeting
from plonemeeting.core.interfaces import IMeetingItem
from plonemeeting.core.migrations.p4top6 import extra_state
from plonemeeting.core.migrations.p4top6 import mappings
from Products.Five import BrowserView
from urllib.parse import unquote
from urllib.parse import urlparse
from zope import schema
from zope.annotation import IAnnotations
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema import getFields
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import IText

import json
import logging
import re


logger = logging.getLogger("plonemeeting.core: p4top6 import")

# where the values of DEFERRED_FIELDS wait for their targets
# collective.iconifiedcategory rebuilds the annex cache
# (categorized_elements) of a container each time an object is added in
# it. The import adds an object with no field, so its content_category is
# empty and the rebuild fails. These two REQUEST keys stop it, the same
# way ToolPloneMeeting.pasteItems does. @@import_pm_post_process builds
# the cache once every annex is there.
DEFER_CATEGORIZED_KEYS = ("defer_update_categorized_elements",
                          "defer_categorized_content_created_event")

# plonemeeting.restapi reads this one: the AT-compat validators
# (validate_<fieldName>) guard what a user types, and the 4.3 site holds
# values they refuse, an item with an optional adviser that is both
# delay aware and not for example. The data of a site that ran for ten
# years is the reference here, not the validators.
SKIP_VALIDATORS_KEY = "skip_at_compat_validators"

# plonemeeting.core reads this one. An add handler works on an object a
# user just filled in a form. The import adds an empty object and writes
# the fields after, and it has the whole state of the 4.3 object, so the
# handler has nothing to compute and must not send a mail.
IMPORTING_KEY = "importingPloneMeetingContent"

DEFERRED_KEY = "plonemeeting.core.p4top6.deferred_fields"

# UID of the 4.3 site -> UID of the new site, for the content the
# profile creates again instead of importing it
UID_MAP_KEY = "plonemeeting.core.p4top6.uid_map"


def _site_url_pattern(site_id):
    """Match a URL of the exported site, whatever host wrote it.

       The export runs as a script, and a serializer that resolves its
       object outside the request acquisition chain writes another host
       than the one of the exported item. The plone.restapi relation
       deserializer only resolves a URL that starts with the portal URL
       of the *importing* site, so every host is normalized here."""
    return re.compile(r"^https?://[^/]+/{0}(?=/|$)".format(re.escape(site_id)))


# a string that holds one of these is text, not a URL
NOT_A_URL = re.compile(r"[\s<>\"\']")


def _rewrite_urls(value, pattern, portal_url):
    """Replace the site URL of p_value by p_portal_url.

       Only a string that is a URL on its own is rewritten: a URL inside
       a rich text keeps the host it was written with, the import does
       not know the public URL of the new site."""
    if isinstance(value, dict):
        return dict((key, _rewrite_urls(sub, pattern, portal_url))
                    for key, sub in value.items())
    if isinstance(value, list):
        return [_rewrite_urls(sub, pattern, portal_url) for sub in value]
    if isinstance(value, str):
        if NOT_A_URL.search(value):
            return value
        return pattern.sub(portal_url, value)
    return value


def _target_object(item):
    """Get the object p_item is imported into, when it is already there.

       collective.exportimport builds the target path from the "@id" of
       an item: it drops the id of the site and resolves the rest
       against the new site."""
    path = urlparse(unquote(item["@id"])).path.strip("/").split("/")[1:]
    if not path:
        return None
    portal = api.portal.get()
    obj = portal.unrestrictedTraverse("/".join(path), None)
    # traversal also finds a view or an acquired attribute
    if obj is None or getattr(obj, "getPhysicalPath", None) is None:
        return None
    if obj.getPhysicalPath() != portal.getPhysicalPath() + tuple(path):
        return None
    return obj


def deferred_store(create=False):
    """Get the deferred values, kept on the portal so they survive the
       commit between two import steps."""
    annotations = IAnnotations(api.portal.get())
    store = annotations.get(DEFERRED_KEY)
    if store is None and create:
        store = annotations[DEFERRED_KEY] = PersistentMapping()
    return store


def uid_map(create=False):
    """Get the UID translation, kept on the portal so it survives the
       commit between two import steps."""
    annotations = IAnnotations(api.portal.get())
    store = annotations.get(UID_MAP_KEY)
    if store is None and create:
        store = annotations[UID_MAP_KEY] = PersistentMapping()
    return store


def _remap_uids(value, uids):
    """Replace every UID of the 4.3 site by the one of the new site."""
    if isinstance(value, dict):
        return dict((key, _remap_uids(sub, uids))
                    for key, sub in value.items())
    if isinstance(value, list):
        return [_remap_uids(sub, uids) for sub in value]
    if isinstance(value, str):
        return uids.get(value, value)
    return value


def apply_deferred_fields(request):
    """Apply every deferred value whose targets exist by now. A value
       that still does not validate stays in the store for a later pass.

       Returns (applied, remaining, missing) counts."""
    store = deferred_store()
    if not store:
        return 0, 0, 0
    applied = remaining = missing = 0
    for uid, fields in list(store.items()):
        obj = api.content.get(UID=uid)
        if obj is None:
            missing += 1
            continue
        still_deferred = {}
        uids = uid_map() or {}
        path = "/".join(obj.getPhysicalPath())
        for name, value in fields.items():
            if uids:
                value = _remap_uids(value, uids)
            # a deferred value is taken out of the data before the hook
            # that gives a Choice its token reads it
            data = _untokenize_choices(obj, {"@id": path, name: value})
            data.pop("@id")
            if name not in data:
                applied += 1
                continue
            # one call per field: a field that does not validate must not
            # hold back the others
            deserializer = getMultiAdapter((obj, request),
                                           IDeserializeFromJson)
            try:
                deserializer(validate_all=False, data=data)
            except Exception as error:
                logger.info("%s of %s deferred again: %s",
                            name, path, error)
                still_deferred[name] = value
            else:
                applied += 1
        if still_deferred:
            store[uid] = still_deferred
            remaining += len(still_deferred)
        else:
            del store[uid]
    return applied, remaining, missing


def _untokenize(value):
    """Get the value behind its JSON form.

       plone.restapi serializes a Choice as {"token": ..., "title": ...}
       and a List of Choice as a list of those."""
    if isinstance(value, dict) and "token" in value:
        return value["token"]
    if isinstance(value, list):
        return [_untokenize(sub) for sub in value]
    return value


def _factory_kwargs(item, names):
    """The values the content factory must set before the object is
       added to its container."""
    kwargs = {}
    for name in names:
        value = item.get(name)
        if value is None:
            continue
        kwargs[name] = _untokenize(value)
    return kwargs


def _rename_packages(value, renames):
    """Rewrite a dotted name whose package moved in Plone 6."""
    if isinstance(value, dict):
        return dict((key, _rename_packages(sub, renames))
                    for key, sub in value.items())
    if isinstance(value, list):
        return [_rename_packages(sub, renames) for sub in value]
    if isinstance(value, str):
        for old_prefix, new_prefix in renames.items():
            if value.startswith(old_prefix):
                return new_prefix + value[len(old_prefix):]
    return value


def _rename_keys(item, name_map):
    for at_name, dx_name in name_map.items():
        if at_name in item and at_name != dx_name:
            item[dx_name] = item.pop(at_name)
    return item


def _unwrap_plain_text(item, field_names):
    """AT TextFields that became schema.Text are exported as
    {"content-type": "text/plain", "data": ...} dicts; DX expects a
    plain string."""
    for name in field_names:
        value = item.get(name)
        if isinstance(value, dict) and "data" in value:
            item[name] = value["data"]
    return item


def _pod_template_md5(obj, item):
    """Give a POD template the md5 of its own file.

       The 4.3 site has templates whose md5 was never computed, the
       fields are required on the new schema, and the invariants of the
       schema are checked against what the payload carries."""
    if not hasattr(aq_base(obj), "current_md5"):
        return item
    md5 = obj.current_md5 or u""
    for name in ("initial_md5", "style_modification_md5"):
        if not item.get(name):
            item[name] = md5
    return item


def _untokenize_choices(obj, item):
    """Give a Choice field its token instead of the whole term.

       plone.restapi serializes a Choice as {"token": ..., "title": ...}
       and reads both forms back, but plonemeeting.restapi stores the
       value before it checks the vocabulary (an AT validator ran after
       the mutator, and the PloneMeeting vocabularies include the stored
       value). The term dict then sits in the field and the next
       vocabulary that reads it fails."""
    fields = {}
    for schema_ in iterSchemata(obj):
        fields.update(getFields(schema_))
    for name, value in list(item.items()):
        field = fields.get(name)
        if field is None:
            continue
        value_type = getattr(field, "value_type", None)
        if not (IChoice.providedBy(field) or IChoice.providedBy(value_type)):
            continue
        value = _untokenize(value)
        # an empty value means "not set" on the 4.3 side. Keeping it
        # would also run the AT validator of the field, and the 4.3 site
        # has items with no category and no group in charge.
        if value in ("", None) or (isinstance(value, list) and not value):
            item.pop(name)
            continue
        # a term the config does not offer any more has a fallback
        fallbacks = mappings.CHOICE_FALLBACKS.get(name)
        if fallbacks and not isinstance(value, list):
            fallback = fallbacks.get(value)
            if fallback is not None and not _in_vocabulary(field, obj, value):
                logger.info("%s: %r is not offered any more, using %r",
                            name, value, fallback)
                value = fallback
        # a term the new site does not offer is not a value either
        if name in mappings.DROP_UNKNOWN_CHOICE_FIELDS and \
                not _in_vocabulary(field, obj, value):
            logger.info("%s: %r is not offered any more on %s",
                        name, value, item.get("@id"))
            item.pop(name)
            continue
        # or, for a list, only the values it does not offer leave
        if name in mappings.DROP_UNKNOWN_CHOICE_VALUES and \
                isinstance(value, list):
            kept = [sub for sub in value if _in_vocabulary(field, obj, sub)]
            if len(kept) != len(value):
                logger.info("%s: %s is not offered any more", name,
                            sorted(set(value) - set(kept)))
            if not kept:
                item.pop(name)
                continue
            value = kept
        item[name] = value
    return item


def _in_vocabulary(field, obj, value):
    """Does the vocabulary of p_field, read on p_obj, hold p_value?"""
    value_type = getattr(field, "value_type", None)
    if IChoice.providedBy(value_type):
        field = value_type
    try:
        vocabulary = field.bind(obj).vocabulary
        vocabulary.getTermByToken(value)
    except Exception:
        return False
    return True


def _drop_missing_required(obj, item):
    """Take out the fields the 4.3 site left empty and Plone 6 requires.

       The plone.restapi deserializer refuses a null for a required
       field. The Dexterity default is the right value for a field the
       source never filled."""
    fields = {}
    for schema_ in iterSchemata(obj):
        fields.update(getFields(schema_))
    for name, value in list(item.items()):
        if value is not None:
            continue
        field = fields.get(name)
        if field is not None and field.required:
            item.pop(name)
    return item


def _adapt_text_fields(obj, item):
    """Give an Archetypes TextField the form its Dexterity field wants.

       The 4.3 export writes {"content-type": ..., "data": ...} for every
       AT TextField. A plain schema.Text wants the string; a RichText
       field wants one of its mime types, and the AT field of an empty
       value says "text/plain", which RichText refuses."""
    fields = {}
    for schema_ in iterSchemata(obj):
        fields.update(getFields(schema_))
    for name, value in list(item.items()):
        field = fields.get(name)
        if field is None:
            continue
        if IRichText.providedBy(field):
            # an AT TextField that was never set comes out as a null, or
            # as a mapping with a null in it. The deserializer of
            # plone.restapi unescapes the data without a check.
            if value is None or (isinstance(value, dict) and
                                 value.get("data") is None):
                item.pop(name)
                continue
            if not isinstance(value, dict):
                continue
            allowed = field.allowed_mime_types
            if allowed and value.get("content-type") not in allowed:
                value["content-type"] = field.default_mime_type
        elif IText.providedBy(field) and isinstance(value, dict) and \
                "data" in value:
            item[name] = value["data"]
    return item


def _known_constrained_types(item, type_ids):
    """Take the types the new site does not have out of the constraints.

       ISelectableConstrainTypes refuses the whole list when one id is
       unknown, so a folder that allows a 4.3 type (MeetingFile, Large
       Plone Folder) would keep none of its types."""
    constrains = item.get("exportimport.constrains")
    if not constrains:
        return item
    for key in ("locally_allowed_types", "immediately_addable_types"):
        values = constrains.get(key)
        if not values:
            continue
        kept = [value for value in values if value in type_ids]
        if len(kept) != len(values):
            logger.info("%s: %s of %s is not a type of the new site",
                        item.get("@id"),
                        sorted(set(values) - set(kept)), key)
        constrains[key] = kept
    return item


def _rename_values(item, field_names, name_map):
    """Rename the *values* of p_field_names, which are AT field names."""
    for name in field_names:
        values = item.get(name)
        if not values:
            continue
        item[name] = [_renamed_token(value, name_map) for value in values]
    return item


def _rename_column_values(item, column_map, name_map):
    """Rename the values of a DataGrid column that holds a field name."""
    for field_name, columns in column_map.items():
        rows = item.get(field_name)
        if not rows:
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            for column in columns:
                if column in row:
                    row[column] = _renamed_token(row[column], name_map)
    return item


def _rename_prefixed_values(item, field_names, name_map):
    """The same, for values that read "MeetingItem.<field name>"."""
    for name in field_names:
        values = item.get(name)
        if not values:
            continue
        item[name] = [_renamed_token(value, name_map, prefixed=True)
                      for value in values]
    return item


def _renamed_token(value, name_map, prefixed=False):
    """Rename a value that is a field name, in both its JSON forms."""
    if isinstance(value, dict) and "token" in value:
        token = _renamed_token(value["token"], name_map, prefixed)
        return token == value["token"] and value or dict(value, token=token)
    if prefixed and isinstance(value, str) and "." in value:
        prefix, name = value.split(".", 1)
        return "%s.%s" % (prefix, _renamed_token(name, name_map))
    return name_map.get(value, value)


def _remap_row_keys(item, row_key_maps):
    """Second, nested camelCase layer: DataGrid row-dict keys."""
    for field_name, key_map in row_key_maps.items():
        rows = item.get(field_name)
        if not rows:
            continue
        for row in rows:
            if isinstance(row, dict):
                for at_key, dx_key in key_map.items():
                    if at_key in row:
                        row[dx_key] = row.pop(at_key)
    return item


def _restore_grid_strings(obj):
    """Put back the empty strings of a data grid row.

       The REST deserializer writes the missing value (None) for an empty
       text column, the 4.3 site stored an empty string, and the code
       that reads a row does row.get(column, '')."""
    for schema_ in iterSchemata(obj):
        for name, field in getFields(schema_).items():
            row_schema = getattr(getattr(field, "value_type", None),
                                 "schema", None)
            if row_schema is None:
                continue
            rows = getattr(aq_base(obj), name, None)
            if not rows:
                continue
            columns = [column for column, sub in getFields(row_schema).items()
                       if IText.providedBy(sub)]
            changed = False
            for row in rows:
                if not hasattr(row, "get"):
                    continue
                for column in columns:
                    if row.get(column, u"") is None:
                        row[column] = u""
                        changed = True
            if changed:
                setattr(obj, name, rows)


class PMImportContent(ImportContent):
    """Import content exported from a Products.PloneMeeting 4.3 site."""

    def start(self):
        self._imported_configs = []
        self._raw_fields = {}
        self._type_ids = set(
            api.portal.get_tool("portal_types").objectIds())
        for key in DEFER_CATEGORIZED_KEYS + (SKIP_VALIDATORS_KEY, IMPORTING_KEY):
            self.request.set(key, True)
        portal = api.portal.get()
        self._url_pattern = _site_url_pattern(portal.getId())
        self._portal_url = portal.absolute_url()
        # an add handler redirects the browser to the referer, unless
        # the form it comes from is an edit form. A scripted request has
        # no referer at all and the read raises.
        self.request.environ.setdefault(
            "HTTP_REFERER", "%s/edit" % self._portal_url)
        deferred_store(create=True)
        uid_map(create=True)

    def _map_uid(self, item):
        """Note the UID an object of the 4.3 site has in the new one.

           Content the profile already created keeps the UID of the new
           site: the contacts directory, the sub-folders of a
           MeetingConfig and every DashboardCollection of its searches.
           A field that points at one of them carries the UID of the 4.3
           site and would not resolve."""
        old_uid = item.get("UID")
        if not old_uid:
            return
        obj = _target_object(item)
        if obj is None:
            # not there: the import creates it with the exported UID
            return
        new_uid = getattr(obj, "UID", None) and obj.UID()
        if new_uid and new_uid != old_uid:
            uid_map(create=True)[old_uid] = new_uid

    def _set_raw_fields(self, obj, item):
        """Set the fields the deserializer cannot validate."""
        fields = self._raw_fields.pop(item.get("UID"), None)
        if not fields:
            return
        for name, value in fields.items():
            setattr(obj, name, value)
        logger.info("Set %s on %s without the deserializer",
                    ", ".join(sorted(fields)),
                    "/".join(obj.getPhysicalPath()))

    def _import_directory(self, item):
        """Apply the fields of the contacts directory on the directory
           the profile already created.

           The import skips existing content, and the directory is the
           first entry of the contacts export, so this runs before the
           held_positions of the same file are deserialized against the
           position_types."""
        directory = _target_object(item)
        if directory is None:
            # not there yet: the import creates it with its fields
            return
        applied = []
        for name in mappings.DIRECTORY_FIELDS:
            value = item.get(name)
            if value is None:
                continue
            setattr(directory, name, value)
            applied.append("%s (%s)" % (name, len(value)))
        if applied:
            logger.info("Set %s on the existing %s",
                        ", ".join(applied),
                        "/".join(directory.getPhysicalPath()))

    def _defer_fields(self, item):
        """Take the fields that point at content which does not exist
           yet out of p_item, and keep them for a later pass."""
        portal_type = item.get("@type", "")
        # the item types are cloned per config: MeetingItemCollege,
        # MeetingItemTemplatebp, ...
        if portal_type.startswith("MeetingItem"):
            portal_type = "MeetingItem"
        names = mappings.DEFERRED_FIELDS.get(portal_type, ())
        uid = item.get("UID")
        if not names or not uid:
            return item
        deferred = {}
        for name in names:
            # an empty value needs no second pass
            if item.get(name):
                deferred[name] = item.pop(name)
        if deferred:
            store = deferred_store(create=True)
            store[uid] = deferred
        return item

    def global_obj_hook_before_deserializing(self, obj, item):
        """Write the blobs before the deserializer runs.

           collective.exportimport sets a blob_path field after
           deserialization. An invariant that wants a file then fails on
           an object that has none yet — a POD template wants an
           odt_file or a template to reuse — and the whole object is
           lost. Write the blob first and take the key out of the data:
           an invariant reads the object for a field the data does not
           carry."""
        blob_fields = [name for name, value in item.items()
                       if isinstance(value, dict) and value.get("blob_path")]
        if blob_fields:
            self.import_blob_paths(obj, item)
            for name in blob_fields:
                item.pop(name)
        item = _adapt_text_fields(obj, item)
        item = _drop_missing_required(obj, item)
        item = _pod_template_md5(obj, item)
        item = _untokenize_choices(obj, item)
        if IMeetingConfig.providedBy(obj):
            self._apply_wf_adaptations(obj, item)
        return obj, item

    def _apply_wf_adaptations(self, cfg, item):
        """Adapt the workflows of a config before its fields are read.

           Many fields of a config point at item states that only exist
           once the workflow adaptations are applied.
           onConfigInitialized() cannot apply them: they are read by
           _performWorkflowAdaptations(), which walks the "searches"
           folders of the config, and that same handler creates those
           folders after it calls registerPortalTypes(). Here they
           exist."""
        value = _untokenize(item.get(mappings.CONFIG_WF_ADAPTATIONS_FIELD))
        if not value:
            return
        setattr(cfg, mappings.CONFIG_WF_ADAPTATIONS_FIELD, value)
        cfg.registerPortalTypes()
        logger.info("Applied %s workflow adaptations on %s",
                    len(value), "/".join(cfg.getPhysicalPath()))

    def get_parent_as_container(self, item):
        """portal_plonemeeting is a tool: the profile creates it, so it
           is not imported content and its UID is not the one of the 4.3
           site. The MeetingConfigs live in it."""
        if item.get("parent", {}).get("@type") == "ToolPloneMeeting":
            return api.portal.get_tool(TOOL_ID)
        return super(PMImportContent, self).get_parent_as_container(item)

    def create_container(self, item):
        """Never invent a container.

           The stock import creates the folders a path needs. Here a
           missing container means the export is incomplete or a step ran
           out of order, and the invented Folder would sit where the real
           object belongs. Report it and skip the item."""
        logger.warning("No container for %s %s: its parent %s is not "
                       "imported", item["@type"], item["@id"],
                       item["parent"].get("@id"))
        return None

    def global_dict_hook(self, item):
        item = _rewrite_urls(item, self._url_pattern, self._portal_url)
        item = _known_constrained_types(item, self._type_ids)
        item = _unwrap_plain_text(
            item, mappings.DUBLIN_CORE_PLAIN_TEXT_FIELDS)
        portal_type = item.get("@type", "")
        self._map_uid(item)
        if portal_type == "MeetingConfig":
            item = _rename_keys(item, mappings.MEETINGCONFIG_AT_TO_DX)
            item = _unwrap_plain_text(
                item, mappings.MEETINGCONFIG_PLAIN_TEXT_FIELDS)
            item = _remap_row_keys(item, mappings.ROW_KEY_MAPS)
            item = _rename_packages(item, mappings.PACKAGE_RENAMES)
            names = dict(mappings.MEETINGITEM_AT_TO_DX)
            names.update(mappings.MEETINGITEM_EXTRA_ATTRIBUTE_NAMES)
            item = _rename_values(
                item, mappings.MEETINGCONFIG_ITEM_FIELD_NAME_FIELDS, names)
            item = _rename_prefixed_values(
                item, mappings.MEETINGCONFIG_PREFIXED_ITEM_FIELD_FIELDS, names)
            item = _rename_column_values(
                item, mappings.MEETINGCONFIG_ITEM_FIELD_NAME_COLUMNS, names)
            raw = {}
            for name in (mappings.MEETINGCONFIG_RAW_GRIDS +
                         mappings.MEETINGCONFIG_RAW_FIELDS):
                if item.get(name):
                    raw[name] = _untokenize(item.pop(name))
            if raw and item.get("UID"):
                self._raw_fields[item["UID"]] = raw
        elif portal_type.startswith("MeetingItem"):
            # covers per-config cloned FTIs (MeetingItemCollege, ...) and
            # the MeetingItemTemplate/MeetingItemRecurring subtypes
            item = _rename_keys(item, mappings.MEETINGITEM_AT_TO_DX)
            item = _unwrap_plain_text(
                item, mappings.MEETINGITEM_PLAIN_TEXT_FIELDS)
            for name in mappings.MEETINGITEM_DROP_AT_IMPORT:
                item.pop(name, None)
        elif portal_type == "directory":
            self._import_directory(item)
        # Meeting* (non item), meetingadvice, annex/annexDecision and
        # contacts types were already DX on Plone 4.3: no rename needed.
        factory_fields = mappings.FACTORY_FIELDS.get(portal_type)
        if factory_fields:
            item["factory_kwargs"] = _factory_kwargs(item, factory_fields)
        return self._defer_fields(item)

    def global_obj_hook(self, obj, item):
        self._set_raw_fields(obj, item)
        _restore_grid_strings(obj)
        # non-schema persistent attributes and annotations dumped by
        # export_p43.py (see extra_state.py)
        extra_state.load_extra_state(obj, item.get(extra_state.EXTRA_STATE_KEY))
        if IMeetingConfig.providedBy(obj):
            self._imported_configs.append(obj.UID())

    def import_review_state(self, obj, item):
        """Do not play the transitions of an object to reach its state.

           collective.exportimport writes the workflow history of the
           object after this, and the state of a DCWorkflow is the state
           of the last entry of that history. A transition is also an
           action: it can put an item in a meeting or send a mail. The
           permissions of the state and the catalog come back in
           @@import_pm_post_process."""

    def finish(self):
        # AT mutators for customAdvisers/powerObservers/committees/
        # usingGroups/wfAdaptations had side effects (Plone group creation,
        # local roles) that now live in event handlers; imports bypass the
        # edit form so trigger them explicitly.
        for uid in self._imported_configs:
            cfg = api.content.get(UID=uid)
            if cfg is not None:
                logger.info("Notifying ObjectModifiedEvent for %s",
                            "/".join(cfg.getPhysicalPath()))
                notify(ObjectModifiedEvent(cfg))
        # the configs are there now, so the item states an organization
        # points at are known: retry what this file deferred, and what an
        # earlier file left behind
        applied, remaining, missing = apply_deferred_fields(self.request)
        logger.info("Deferred fields: %s applied, %s waiting, %s objects "
                    "not imported", applied, remaining, missing)
        for key in DEFER_CATEGORIZED_KEYS + (SKIP_VALIDATORS_KEY, IMPORTING_KEY):
            self.request.set(key, False)


class ImportManuallyLinkedItems(BrowserView):
    """Rebuild MeetingItem.manually_linked_items (a list of UIDs) from the
    @@export_relations JSON of the Plone 4.3 site.

    The AT field was a ReferenceField (relationship 'ManuallyLinkedItem');
    its rows in relations.json look like:
    {"from_uuid": ..., "to_uuid": ..., "relationship": "ManuallyLinkedItem"}
    Call as @@import_pm_manually_linked_items?path=/path/to/relations.json
    """

    RELATIONSHIP = "ManuallyLinkedItem"

    def __call__(self):
        path = self.request.form.get("path")
        if not path:
            return "Pass ?path=/absolute/path/to/relations.json"
        with open(path) as f:
            relations = json.load(f)
        linked = {}
        for rel in relations:
            if rel.get("relationship") != self.RELATIONSHIP:
                continue
            linked.setdefault(rel["from_uuid"], []).append(rel["to_uuid"])
        done = missing = 0
        for from_uid, to_uids in linked.items():
            obj = api.content.get(UID=from_uid)
            if obj is None:
                logger.warning("No object found for UID %s", from_uid)
                missing += 1
                continue
            # only keep targets that were actually imported
            existing = [uid for uid in to_uids
                        if api.content.get(UID=uid) is not None]
            obj.manually_linked_items = existing
            obj.reindexObject(idxs=["manually_linked_items"])
            done += 1
        msg = "manually_linked_items set on %s items (%s source UIDs " \
            "not found)" % (done, missing)
        logger.info(msg)
        return msg


class ImportToolSettings(BrowserView):
    """Import portal_plonemeeting settings from a JSON dump of the 4.3
    tool (see MIGRATION_DATA.md for the export snippet). The dump maps
    DX snake_case attribute names to values.

    Call as @@import_pm_tool_settings?path=/path/to/tool.json
    """

    def __call__(self):
        path = self.request.form.get("path")
        if not path:
            return "Pass ?path=/absolute/path/to/tool.json"
        with open(path) as f:
            settings = json.load(f)
        tool = api.portal.get_tool("portal_plonemeeting")
        for name, value in settings.items():
            if isinstance(value, list):
                # JSON has no tuples; stored AT values were tuples
                value = tuple(value)
            setattr(tool, name, value)
        msg = "portal_plonemeeting: %s attributes set" % len(settings)
        logger.info(msg)
        return msg


class ImportRegistry(BrowserView):
    """Set the plone.registry records exported by export_other_p43.py.

    The records come as a list, in the order they must be written:
    "organizations" first, because the rows of "functions" point at
    selected organizations. Writing them fires the
    collective.contact.plonegroup subscriber that creates the Plone
    groups of every organization, so the contacts must be imported
    first.

    Call as @@import_pm_registry?path=/path/to/registry.json
    """

    def __call__(self):
        path = self.request.form.get("path")
        if not path:
            return "Pass ?path=/absolute/path/to/registry.json"
        with open(path) as f:
            records = json.load(f)
        registry = getUtility(IRegistry)
        done = []
        for record in records:
            name = record["name"]
            value = record["value"]
            if name not in registry.records:
                logger.warning("The registry has no record %s", name)
                continue
            field = registry.records[name].field
            # JSON has no tuple
            if isinstance(field, schema.Tuple) and isinstance(value, list):
                value = tuple(value)
            try:
                registry[name] = value
            except Exception as error:
                # a value that points at content which is not imported
                # does not validate; the other records must still be set
                logger.warning("The registry record %s was not set: %s",
                               name, error)
                continue
            done.append(name)
            logger.info("Set the registry record %s", name)
        msg = "registry: %s of %s records set" % (len(done), len(records))
        logger.info(msg)
        return msg


class ImportDeferredFields(BrowserView):
    """Apply the fields the content import could not set because their
    targets did not exist yet (see mappings.DEFERRED_FIELDS).

    Every import run already retries them when it ends. Call this view
    for a last pass once every file is imported, and to see what is
    left:  @@import_pm_deferred_fields
    """

    def __call__(self):
        # the deferred values are 4.3 data like the rest of the import
        self.request.set(SKIP_VALIDATORS_KEY, True)
        try:
            applied, remaining, missing = apply_deferred_fields(self.request)
        finally:
            self.request.set(SKIP_VALIDATORS_KEY, False)
        msg = "deferred fields: %s applied, %s still waiting, %s on " \
            "objects that were not imported" % (applied, remaining, missing)
        logger.info(msg)
        return msg


def init_meeting_folders():
    """Make every Members/<user>/mymeetings/<cfg_id> folder a meeting folder.

       The export gives back a plain folder: the meeting_config property,
       the faceted dashboard, the permissions, the constrained types and
       the local roles are not in the JSON. The property is the one the
       tool reads to know which MeetingConfig an object belongs to, so
       this must run before the items are imported."""
    tool = api.portal.get_tool("portal_plonemeeting")
    members = api.portal.get_tool("portal_membership").getMembersFolder()
    cfg_ids = tool.objectIds("MeetingConfig")
    done = 0
    if members is None:
        return done
    for home_folder in members.objectValues():
        root_folder = getattr(aq_base(home_folder), ROOT_FOLDER, None)
        if root_folder is None:
            continue
        root_folder = home_folder[ROOT_FOLDER]
        tool.init_meeting_root_folder(root_folder)
        for cfg_id in cfg_ids:
            if getattr(aq_base(root_folder), cfg_id, None) is None:
                continue
            logger.info("Initializing meeting folder %s",
                        "/".join(root_folder[cfg_id].getPhysicalPath()))
            tool.init_meeting_config_folder(root_folder[cfg_id], tool[cfg_id])
            done += 1
    return done


class ImportMeetingFolders(BrowserView):
    """Make the imported member folders meeting folders.

    Call as @@import_pm_meeting_folders after the folders are imported
    and before the items are.
    """

    def __call__(self):
        msg = "%s meeting folders initialized" % init_meeting_folders()
        logger.info(msg)
        return msg


class ImportPostProcess(BrowserView):
    """Re-apply the PloneMeeting setup that the JSON import cannot carry.

    - User meeting folders (Members/<user>/mymeetings/<cfg_id>) come back
      as plain folders: re-apply the faceted dashboard, the meeting_config
      property, permissions, constrained types and local roles, and the
      constraints of the "mymeetings" root folder.
    - Give back to every object the permissions of its review state, and
      put that state in the catalog.
    - Rebuild the collective.iconifiedcategory annex caches
      (categorized_elements) on every item and meeting, unless called
      with ?skip_categorized_elements=1.

    Call as @@import_pm_post_process once every content is imported,
    before the catalog rebuild.
    """

    def _update_workflow_security(self):
        """Give back to every object the permissions of its review state.

           The review state comes from the workflow history, and
           collective.exportimport writes that history after the object
           is created. The object keeps the permissions of the initial
           state, and the catalog keeps its review state."""
        wf_tool = api.portal.get_tool("portal_workflow")
        count = wf_tool.updateRoleMappings()
        catalog = api.portal.get_tool("portal_catalog")
        for brain in catalog.unrestrictedSearchResults():
            obj = brain._unrestrictedGetObject()
            # the index and the metadata of the catalog, not the
            # modification date: reindexObject only touches it when it
            # gets no index at all
            obj.reindexObject(idxs=["review_state"])
        return count

    def _update_categorized_elements(self):
        """Build the annex cache of every container that can hold one.

           Every item and meeting gets one, empty when it has no annex.
           An annex can also be in an advice, so add the parent of each
           annex that is not in an item or a meeting."""
        catalog = api.portal.get_tool("portal_catalog")
        containers = {}
        for brain in catalog.unrestrictedSearchResults(
                object_provides=[IMeetingItem.__identifier__,
                                 IMeeting.__identifier__]):
            obj = brain._unrestrictedGetObject()
            containers["/".join(obj.getPhysicalPath())] = obj
        for brain in catalog.unrestrictedSearchResults(
                object_provides=IIconifiedCategorizationMarker.__identifier__):
            parent = aq_parent(aq_inner(brain._unrestrictedGetObject()))
            containers.setdefault("/".join(parent.getPhysicalPath()), parent)
        for container in containers.values():
            update_all_categorized_elements(container)
        return len(containers)

    def _update_category_icons(self):
        """Build the icon scale and the CSS of the annex types.

           collective.iconifiedcategory does it when a category is
           created, and the import creates the object before it writes
           the icon."""
        catalog = api.portal.get_tool("portal_catalog")
        done = 0
        for brain in catalog.unrestrictedSearchResults(
                object_provides=[ICategory.__identifier__,
                                 ISubcategory.__identifier__]):
            category = brain._unrestrictedGetObject()
            try:
                category.restrictedTraverse("@@images").scale(scale="listing")
            except Exception as error:
                logger.warning("No icon scale for %s: %s",
                               "/".join(category.getPhysicalPath()), error)
                continue
            done += 1
        _cookCssResources()
        return done

    def __call__(self):
        folders = init_meeting_folders()
        msg = "%s meeting folders initialized" % folders
        objects = self._update_workflow_security()
        msg += ", %s objects got the permissions of their state" % objects
        icons = self._update_category_icons()
        msg += ", %s annex type icons built" % icons
        if not self.request.form.get("skip_categorized_elements"):
            containers = self._update_categorized_elements()
            msg += ", categorized_elements updated on %s items and meetings" % containers
        logger.info(msg)
        return msg
