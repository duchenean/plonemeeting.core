# -*- coding: utf-8 -*-
"""collective.exportimport import-side customizations.

Registered (zcml:condition="installed collective.exportimport") as
@@import_content on the PloneMeeting browser layer, overriding the
stock view. All AT camelCase -> DX snake_case transforms happen here,
at import time — the exported JSON stays faithful to the Plone 4.3
source (see MIGRATION_DATA.md at the buildout root).
"""

import json
import logging

from Products.Five import BrowserView
from plone import api
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from collective.exportimport.import_content import ImportContent

from plonemeeting.core.content.meetingconfig import IMeetingConfig
from plonemeeting.core.migrations.p4top6 import extra_state
from plonemeeting.core.migrations.p4top6 import mappings

logger = logging.getLogger("plonemeeting.core: p4top6 import")


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


class PMImportContent(ImportContent):
    """Import content exported from a Products.PloneMeeting 4.3 site."""

    def start(self):
        self._imported_configs = []

    def global_dict_hook(self, item):
        portal_type = item.get("@type", "")
        if portal_type == "MeetingConfig":
            item = _rename_keys(item, mappings.MEETINGCONFIG_AT_TO_DX)
            item = _unwrap_plain_text(
                item, mappings.MEETINGCONFIG_PLAIN_TEXT_FIELDS)
            item = _remap_row_keys(item, mappings.ROW_KEY_MAPS)
        elif portal_type.startswith("MeetingItem"):
            # covers per-config cloned FTIs (MeetingItemCollege, ...) and
            # the MeetingItemTemplate/MeetingItemRecurring subtypes
            item = _rename_keys(item, mappings.MEETINGITEM_AT_TO_DX)
            item = _unwrap_plain_text(
                item, mappings.MEETINGITEM_PLAIN_TEXT_FIELDS)
            for name in mappings.MEETINGITEM_DROP_AT_IMPORT:
                item.pop(name, None)
        # Meeting* (non item), meetingadvice, annex/annexDecision and
        # contacts types were already DX on Plone 4.3: no rename needed.
        return item

    def global_obj_hook(self, obj, item):
        # non-schema persistent attributes and annotations dumped by
        # export_p43.py (see extra_state.py)
        extra_state.load_extra_state(obj, item.get(extra_state.EXTRA_STATE_KEY))
        if IMeetingConfig.providedBy(obj):
            self._imported_configs.append(obj.UID())

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
