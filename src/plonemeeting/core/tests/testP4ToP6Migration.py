# -*- coding: utf-8 -*-
"""Tests for the P4 -> P6 collective.exportimport hooks.

Dict-transform tests and mapping invariants against the DX schemas
(no Plone layer), plus extra-state round-trips on real content.
"""

from collective.contact.plonegroup.config import PLONEGROUP_ORG
from plone import api
from plone.behavior.interfaces import IBehavior
from plone.dexterity.interfaces import IDexterityFTI
from plonemeeting.core.content.meetingconfig import IMeetingConfig
from plonemeeting.core.content.meetingitem import IMeetingItem
from plonemeeting.core.migrations.p4top6 import mappings
from plonemeeting.core.migrations.p4top6.import_content import _remap_row_keys
from plonemeeting.core.migrations.p4top6.import_content import _rename_keys
from plonemeeting.core.migrations.p4top6.import_content import _rewrite_urls
from plonemeeting.core.migrations.p4top6.import_content import _site_url_pattern
from plonemeeting.core.migrations.p4top6.import_content import _unwrap_plain_text
from plonemeeting.core.tests.PloneMeetingTestCase import PloneMeetingTestCase
from zope.component import getUtility
from zope.component import queryUtility
from zope.schema import getFieldNames

import unittest


class TestMappingInvariants(unittest.TestCase):
    """A mapping that targets a nonexistent DX field means silent data
    loss at import: every DX name must exist on the DX schema."""

    def test_meetingitem_targets_exist(self):
        schema_names = set(getFieldNames(IMeetingItem))
        targets = set(mappings.MEETINGITEM_AT_TO_DX.values())
        self.assertEqual(targets - schema_names, set())

    def test_meetingconfig_targets_exist(self):
        schema_names = set(getFieldNames(IMeetingConfig))
        targets = set(mappings.MEETINGCONFIG_AT_TO_DX.values())
        self.assertEqual(targets - schema_names, set())

    def test_plain_text_fields_exist(self):
        self.assertEqual(
            mappings.MEETINGITEM_PLAIN_TEXT_FIELDS -
            set(getFieldNames(IMeetingItem)), set())
        self.assertEqual(
            mappings.MEETINGCONFIG_PLAIN_TEXT_FIELDS -
            set(getFieldNames(IMeetingConfig)), set())

    def test_meetingconfig_field_tables_exist(self):
        """Every table that names MeetingConfig fields must name real
           ones: a name that no longer exists is a value the import
           silently leaves behind."""
        schema_names = set(getFieldNames(IMeetingConfig))
        for table in (mappings.MEETINGCONFIG_RAW_GRIDS,
                      mappings.MEETINGCONFIG_RAW_FIELDS,
                      mappings.MEETINGCONFIG_ITEM_FIELD_NAME_FIELDS,
                      mappings.MEETINGCONFIG_PREFIXED_ITEM_FIELD_FIELDS,
                      tuple(mappings.MEETINGCONFIG_ITEM_FIELD_NAME_COLUMNS)):
            self.assertEqual(set(table) - schema_names, set())

    def test_row_key_map_grids_exist(self):
        self.assertEqual(
            set(mappings.ROW_KEY_MAPS) - set(getFieldNames(IMeetingConfig)),
            set())

    def test_meetingconfig_mapping_agrees_with_the_class(self):
        """content/meetingconfig.py keeps its own AT -> DX table for the
           dynamic lookups. Two tables that disagree mean a field that
           the import renames to nothing: "wfAdaptations" is a class
           attribute of the 4.2 MeetingConfig (every available
           adaptation), the field is "workflowAdaptations"."""
        from plonemeeting.core.content.meetingconfig import _AT_CAMEL_TO_DX_SNAKE

        disagree = {}
        for at_name, dx_name in _AT_CAMEL_TO_DX_SNAKE.items():
            if at_name == dx_name:
                # identity pairs are left out of the migration mapping
                continue
            if mappings.MEETINGCONFIG_AT_TO_DX.get(at_name) != dx_name:
                disagree[at_name] = dx_name
        self.assertEqual(disagree, {})

    def test_directory_fields_exist(self):
        from collective.contact.core.content.directory import IDirectory
        self.assertEqual(
            set(mappings.DIRECTORY_FIELDS) - set(getFieldNames(IDirectory)),
            set())

    def test_no_duplicate_targets(self):
        for name_map in (mappings.MEETINGITEM_AT_TO_DX,
                         mappings.MEETINGCONFIG_AT_TO_DX):
            targets = list(name_map.values())
            self.assertEqual(len(targets), len(set(targets)))


class TestTransforms(unittest.TestCase):

    def test_rename_keys(self):
        item = {"budgetRelated": True, "decision": "x", "@type": "MeetingItemCollege"}
        _rename_keys(item, mappings.MEETINGITEM_AT_TO_DX)
        self.assertNotIn("budgetRelated", item)
        self.assertTrue(item["budget_related"])
        self.assertEqual(item["decision"], "x")

    def test_unwrap_plain_text(self):
        item = {"item_assembly":
                {"content-type": "text/plain", "data": "Mr X, Mrs Y"},
                "item_signatures": "already plain"}
        _unwrap_plain_text(item, mappings.MEETINGITEM_PLAIN_TEXT_FIELDS)
        self.assertEqual(item["item_assembly"], "Mr X, Mrs Y")
        self.assertEqual(item["item_signatures"], "already plain")

    def test_remap_row_keys(self):
        item = {"certified_signatures": [
            {"signatureNumber": "1", "name": "N", "held_position": "hp"},
            {"signatureNumber": "2", "name": "M"}]}
        _remap_row_keys(item, mappings.ROW_KEY_MAPS)
        rows = item["certified_signatures"]
        self.assertEqual([r["signature_number"] for r in rows], ["1", "2"])
        self.assertNotIn("signatureNumber", rows[0])
        self.assertEqual(rows[0]["held_position"], "hp")

    def test_remap_row_keys_handles_missing_and_none(self):
        item = {"certified_signatures": None}
        _remap_row_keys(item, mappings.ROW_KEY_MAPS)  # must not raise
        _remap_row_keys({}, mappings.ROW_KEY_MAPS)


class TestExtraStateCodec(unittest.TestCase):
    """encode()/decode() round-trips for the non-schema state codec."""

    def _round_trip(self, value):
        from plonemeeting.core.migrations.p4top6 import extra_state

        import json
        return extra_state.decode(json.loads(json.dumps(extra_state.encode(value))))

    def test_scalars_and_text(self):
        for value in (None, True, 3, 2.5, u"héhé"):
            self.assertEqual(self._round_trip(value), value)
        # py2 utf-8 bytes become text
        self.assertEqual(self._round_trip(u"héhé".encode("utf-8")), u"héhé")

    def test_dates(self):
        from DateTime import DateTime

        import datetime
        dt = DateTime("2024/03/05 14:15:16.123456 GMT+2")
        res = self._round_trip(dt)
        self.assertTrue(isinstance(res, DateTime))
        self.assertEqual(res.timeTime(), dt.timeTime())
        self.assertEqual(res.timezone(), dt.timezone())
        d = datetime.datetime(2024, 3, 5, 14, 15, 16, 123456)
        self.assertEqual(self._round_trip(d), d)
        self.assertEqual(self._round_trip(d.date()), d.date())

    def test_containers_keep_their_type(self):
        from collections import OrderedDict
        from persistent.list import PersistentList
        from persistent.mapping import PersistentMapping
        pm = PersistentMapping()
        pm["a"] = PersistentList([1, 2, {"x": (1, 2)}])
        pm[3] = OrderedDict([("z", 1), ("y", set(["s"]))])
        res = self._round_trip(pm)
        self.assertTrue(isinstance(res, PersistentMapping))
        self.assertTrue(isinstance(res["a"], PersistentList))
        self.assertEqual(res["a"][2], {"x": (1, 2)})
        self.assertTrue(isinstance(res["a"][2]["x"], tuple))
        self.assertTrue(isinstance(res[3], OrderedDict))
        self.assertEqual(list(res[3].keys()), ["z", "y"])
        self.assertEqual(res[3]["y"], set(["s"]))
        # int keys survive JSON
        self.assertTrue(3 in res)

    def test_unsupported_value_is_skipped(self):
        from plonemeeting.core.migrations.p4top6 import extra_state
        encoded = extra_state.encode({"o": object()})
        self.assertEqual(encoded["items"][0][1][extra_state.TYPE_KEY], "unsupported")
        self.assertEqual(self._round_trip({"o": object()}), {"o": None})

    def test_attrs_for_portal_type(self):
        from plonemeeting.core.migrations.p4top6 import extra_state
        self.assertEqual(extra_state.attrs_for_portal_type("MeetingItemPma"),
                         extra_state.ITEM_ATTRS)
        self.assertEqual(extra_state.attrs_for_portal_type("MeetingItemTemplatePma"),
                         extra_state.ITEM_ATTRS)
        self.assertEqual(extra_state.attrs_for_portal_type("MeetingPma"),
                         extra_state.MEETING_ATTRS)
        self.assertEqual(extra_state.attrs_for_portal_type("meetingadvicefinances"),
                         extra_state.ADVICE_ATTRS)
        self.assertEqual(extra_state.attrs_for_portal_type("MeetingConfig"), ())
        self.assertEqual(extra_state.attrs_for_portal_type("Folder"), ())


class TestFactoryKwargs(unittest.TestCase):
    """A MeetingConfig must carry the fields PloneMeeting reads when the
       object is added, before the deserializer runs."""

    def test_tokens_are_decoded(self):
        from plonemeeting.core.migrations.p4top6.import_content import _factory_kwargs

        item = {"short_name": "College",
                "item_workflow": {"title": "meetingitem_workflow",
                                  "token": "meetingitem_workflow"},
                "wf_adaptations": [{"title": "Refused (refused)",
                                    "token": "refused"}],
                "config_group": {"title": "None", "token": ""},
                "meeting_workflow": None,
                "title": u"Coll\xe8ge"}
        res = _factory_kwargs(item, ("short_name", "title", "item_workflow",
                                     "meeting_workflow", "wf_adaptations",
                                     "config_group", "absent"))
        self.assertEqual(res, {"short_name": "College",
                               "title": u"Coll\xe8ge",
                               "item_workflow": "meetingitem_workflow",
                               "wf_adaptations": ["refused"],
                               "config_group": ""})


class TestValueRenaming(unittest.TestCase):
    """A MeetingConfig also stores MeetingItem field *names* as values."""

    def test_rename_values(self):
        from plonemeeting.core.migrations.p4top6.import_content import _rename_values

        item = {"used_item_attributes": [
            {"title": "Description (description)", "token": "description"},
            {"title": "x", "token": "sendToAuthority"},
            "toDiscuss",
            "already_snake"]}
        res = _rename_values(item, ("used_item_attributes", "absent"),
                             mappings.MEETINGITEM_AT_TO_DX)
        self.assertEqual(
            [v["token"] if isinstance(v, dict) else v
             for v in res["used_item_attributes"]],
            ["description", "send_to_authority", "to_discuss",
             "already_snake"])

    def test_rename_prefixed_values(self):
        from plonemeeting.core.migrations.p4top6.import_content import _rename_prefixed_values

        item = {"xhtml_transform_fields": [
            {"title": "x", "token": "MeetingItem.detailedDescription"},
            "MeetingItem.copyGroups",
            "Meeting.observations"]}
        res = _rename_prefixed_values(item, ("xhtml_transform_fields", ),
                                      mappings.MEETINGITEM_AT_TO_DX)
        self.assertEqual(
            [v["token"] if isinstance(v, dict) else v
             for v in res["xhtml_transform_fields"]],
            ["MeetingItem.detailed_description", "MeetingItem.copy_groups",
             "Meeting.observations"])

    def test_rename_column_values(self):
        from plonemeeting.core.migrations.p4top6.import_content import _rename_column_values

        item = {"item_fields_config": [{"name": "neededFollowUp",
                                        "view": "python: True"}]}
        res = _rename_column_values(
            item, {"item_fields_config": ("name", )},
            mappings.MEETINGITEM_AT_TO_DX)
        self.assertEqual(res["item_fields_config"][0]["name"],
                         "needed_follow_up")
        self.assertEqual(res["item_fields_config"][0]["view"], "python: True")


class TestUidRemapping(unittest.TestCase):
    """Content the profile creates again keeps the UID of the new site."""

    def test_remap_uids(self):
        from plonemeeting.core.migrations.p4top6.import_content import _remap_uids

        uids = {"old-uid": "new-uid"}
        value = [{"token": "old-uid", "title": "A search"},
                 "old-uid", "another-uid", 3, None]
        self.assertEqual(
            _remap_uids(value, uids),
            [{"token": "new-uid", "title": "A search"},
             "new-uid", "another-uid", 3, None])


class TestUrlRewriting(unittest.TestCase):
    """Export and import must agree on the URL of the site, whatever
       host the serializer that wrote a value used."""

    def test_export_pattern_matches_any_host(self):
        from plonemeeting.core.migrations.p4top6.export_p43 import flatten_urls
        from plonemeeting.core.migrations.p4top6.export_p43 import site_url_pattern

        pattern = site_url_pattern("/demo/demo")
        item = {"@id": "http://nohost/demo/demo/contacts",
                "position": {"@id": "http://foo/demo/demo/contacts/org"},
                "rows": [{"url": "https://delib.example.be/demo/demo/x"}],
                "other": "http://nohost/demo/demofoo/keep",
                "number": 3}
        res = flatten_urls(item, pattern, "http://nohost/Plone")
        self.assertEqual(res["@id"], "http://nohost/Plone/contacts")
        self.assertEqual(res["position"]["@id"],
                         "http://nohost/Plone/contacts/org")
        self.assertEqual(res["rows"][0]["url"], "http://nohost/Plone/x")
        # "/demo/demofoo" is another path, not the site
        self.assertEqual(res["other"], "http://nohost/demo/demofoo/keep")
        self.assertEqual(res["number"], 3)

    def test_import_rewrites_whole_urls_only(self):
        pattern = _site_url_pattern("Plone")
        item = {"@id": "http://nohost/Plone/contacts",
                "position": {"@id": "http://foo/Plone/contacts/org"},
                "text": u'see <a href="http://nohost/Plone/x">x</a>',
                "keep": "http://nohost/Plonebis/x"}
        res = _rewrite_urls(item, pattern, "http://site.be/Plone")
        self.assertEqual(res["@id"], "http://site.be/Plone/contacts")
        self.assertEqual(res["position"]["@id"],
                         "http://site.be/Plone/contacts/org")
        # a URL inside a rich text keeps its host, the import does not
        # know the public URL of the new site
        self.assertEqual(res["text"],
                         u'see <a href="http://nohost/Plone/x">x</a>')
        self.assertEqual(res["keep"], "http://nohost/Plonebis/x")


class TestExportScriptHelpers(unittest.TestCase):
    """export_p43 helpers that must work before the export view runs."""

    def test_prepare_request_forces_post(self):
        from plonemeeting.core.migrations.p4top6 import export_p43

        class Request(dict):
            def __init__(self):
                super(Request, self).__init__()
                self.environ = {"REQUEST_METHOD": "GET"}
                self.form = {}

        class Portal(object):
            def absolute_url(self):
                return "http://nohost/plone"

        request = Request()
        export_p43.prepare_request(request, Portal(), "pm.json")
        self.assertEqual(request.environ["REQUEST_METHOD"], "POST")
        self.assertEqual(request.method, "POST")
        self.assertTrue(request.form["form.submitted"])
        self.assertEqual(request.form["filename"], "pm.json")
        # the unexported paths go to their own file, not into the
        # content file the import reads
        self.assertTrue("write_errors" not in request.form)
        self.assertEqual(request["ACTUAL_URL"], "http://nohost/plone")

    def test_portal_types_with_content_sets_query_attributes(self):
        from plonemeeting.core.migrations.p4top6 import export_p43

        class View(object):
            def portal_types(self):
                # build_query() needs these three attributes
                self.seen = (self.portal_type, self.path, self.depth)
                return [{"value": "MeetingConfig"}, {"value": "Folder"}]

        class Portal(object):
            def getPhysicalPath(self):
                return ("", "plone")

        view = View()
        res = export_p43.portal_types_with_content(view, Portal())
        self.assertEqual(res, ["MeetingConfig", "Folder"])
        self.assertEqual(view.seen, ([], "/plone", -1))


class TestExtraStateRoundTrip(PloneMeetingTestCase):
    """dump_extra_state()/load_extra_state() on real content, through
       the export hook and the import hook."""

    def _json_round_trip(self, state):
        import json
        return json.loads(json.dumps(state))

    def test_item_extra_state(self):
        from ftw.labels.interfaces import ILabeling
        from persistent.mapping import PersistentMapping
        from plonemeeting.core.migrations.p4top6 import extra_state
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem", optionalAdvisers=(self.vendors_uid, ))
        self.assertTrue(self.vendors_uid in item.adviceIndex)
        item.takenOverByInfos["itemcreated"] = "pmCreator1"
        item.itemHistory.append({"action": "test"})
        ILabeling(item).storage["label"] = PersistentMapping()
        item._setSentToOtherMC = None
        ann_key = item._getSentToOtherMCAnnotationKey(self.meetingConfig2.getId())
        from zope.annotation.interfaces import IAnnotations
        IAnnotations(item)[ann_key] = "some-uid"

        state = self._json_round_trip(extra_state.dump_extra_state(item))
        exported_attrs = set(state["attributes"].keys())
        self.assertTrue(set(["adviceIndex", "autoCopyGroups", "itemHistory",
                             "takenOverByInfos", "emergency_changes_history",
                             "completeness_changes_history"]).issubset(exported_attrs))
        self.assertTrue(exported_attrs.issubset(set(extra_state.ITEM_ATTRS)))
        self.assertEqual(sorted(state["annotations"].keys()),
                         sorted([ann_key, "ftw.labels:labeling"]))

        target = self.create("MeetingItem")
        self.assertFalse(self.vendors_uid in target.adviceIndex)
        extra_state.load_extra_state(target, state)
        self.assertEqual(target.adviceIndex, item.adviceIndex)
        self.assertTrue(isinstance(target.adviceIndex, PersistentMapping))
        self.assertEqual(target.takenOverByInfos, item.takenOverByInfos)
        self.assertEqual(list(target.itemHistory), list(item.itemHistory))
        self.assertEqual(ILabeling(target).storage, ILabeling(item).storage)
        self.assertEqual(IAnnotations(target)[ann_key], "some-uid")

    def test_meeting_extra_state(self):
        from collections import OrderedDict
        from persistent.mapping import PersistentMapping
        from plonemeeting.core.migrations.p4top6 import extra_state
        self.changeUser("pmManager")
        meeting = self.create("Meeting")
        meeting.item_absents["item-uid"] = ["hp-uid-1"]
        meeting.item_signatories["item-uid"] = PersistentMapping({1: "hp-uid-2"})
        meeting.ordered_contacts = OrderedDict([("hp-uid-1", {"attendee": True})])
        meeting._number_of_items = 4

        state = self._json_round_trip(extra_state.dump_extra_state(meeting))
        target = self.create("Meeting")
        extra_state.load_extra_state(target, state)
        self.assertEqual(target.item_absents, meeting.item_absents)
        self.assertEqual(target.item_signatories["item-uid"], {1: "hp-uid-2"})
        self.assertTrue(isinstance(target.item_signatories["item-uid"], PersistentMapping))
        self.assertEqual(target.ordered_contacts, meeting.ordered_contacts)
        self.assertTrue(isinstance(target.ordered_contacts, OrderedDict))
        self.assertEqual(target._number_of_items, 4)

    def test_export_and_import_hooks(self):
        from plonemeeting.core.migrations.p4top6 import extra_state
        from plonemeeting.core.migrations.p4top6.export_p43 import PMExportContent
        from plonemeeting.core.migrations.p4top6.import_content import PMImportContent
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem", optionalAdvisers=(self.vendors_uid, ))
        exported = PMExportContent(self.portal, self.request).global_dict_hook(
            {"@type": item.portal_type}, item)
        self.assertTrue(extra_state.EXTRA_STATE_KEY in exported)
        exported = self._json_round_trip(exported)

        target = self.create("MeetingItem")
        importer = PMImportContent(self.portal, self.request)
        importer.start()
        importer.global_obj_hook(target, exported)
        self.assertEqual(target.adviceIndex, item.adviceIndex)
        # an item without extra state is left untouched
        importer.global_obj_hook(target, {"@type": item.portal_type})
        self.assertEqual(target.adviceIndex, item.adviceIndex)


class TestExtraStateDecoding(unittest.TestCase):
    """The JSON reader of collective.exportimport is simplejson: every
    JSON float comes back as a Decimal."""

    def test_a_json_float_is_read_back_as_a_float(self):
        from decimal import Decimal
        from DateTime import DateTime
        from plonemeeting.core.migrations.p4top6 import extra_state
        value = extra_state.decode(
            {extra_state.TYPE_KEY: "DateTime",
             "ts": Decimal("1668676176.549931"),
             "tz": "GMT+1"})
        self.assertTrue(isinstance(value, DateTime))
        self.assertEqual(value.timezone(), "GMT+1")
        self.assertEqual(extra_state.decode(Decimal("1.5")), 1.5)
        self.assertEqual(extra_state.decode([Decimal("2")]), [2.0])


class TestGridStrings(PloneMeetingTestCase):
    """The REST deserializer writes None for an empty text column, the
    4.3 site stored an empty string."""

    def test_empty_grid_columns_are_strings_again(self):
        from plonemeeting.core.migrations.p4top6.import_content import \
            _restore_grid_strings
        cfg = self.meetingConfig
        self.changeUser("siteadmin")
        cfg.custom_advisers = [
            {"row_id": "unique_id_001",
             "org": self.vendors_uid,
             "gives_auto_advice_on": None,
             "gives_auto_advice_on_help_message": None,
             "for_item_created_from": "2020/01/01",
             "delay": None}]
        _restore_grid_strings(cfg)
        row = cfg.custom_advisers[0]
        self.assertEqual(row["gives_auto_advice_on"], u"")
        self.assertEqual(row["delay"], u"")
        # a column that holds a value and a column that is not there are
        # left alone
        self.assertEqual(row["for_item_created_from"], "2020/01/01")
        self.assertEqual(row["org"], self.vendors_uid)
        self.assertFalse("available_on" in row)


class TestImportPostProcess(PloneMeetingTestCase):
    """@@import_pm_post_process re-initializes imported user folders."""

    def _plain_imported_folders(self, user_id, cfg_id):
        """Mimic what the JSON import leaves behind: plain folders."""
        from plonemeeting.core.config import ROOT_FOLDER
        mtool = self.portal.portal_membership
        if mtool.getHomeFolder(user_id) is None:
            if not mtool.getMemberareaCreationFlag():
                mtool.setMemberareaCreationFlag()
            mtool.createMemberArea(user_id)
        home = mtool.getHomeFolder(user_id)
        if ROOT_FOLDER not in home.objectIds():
            home.invokeFactory("Folder", ROOT_FOLDER, title="My meetings")
        root = home[ROOT_FOLDER]
        if cfg_id not in root.objectIds():
            root.invokeFactory("Folder", cfg_id, title="Imported")
        return root, root[cfg_id]

    def test_post_process_initializes_meeting_folders(self):
        from eea.facetednavigation.interfaces import IFacetedNavigable
        from plonemeeting.core.config import MEETING_CONFIG
        from plonemeeting.core.config import MEETINGMANAGERS_GROUP_SUFFIX
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        self.changeUser("siteadmin")
        root, mc_folder = self._plain_imported_folders("pmCreator2", cfg_id)
        self.assertFalse(IFacetedNavigable.providedBy(mc_folder))
        self.assertFalse(mc_folder.hasProperty(MEETING_CONFIG))

        view = self.portal.restrictedTraverse("@@import_pm_post_process")
        self.request.form["skip_categorized_elements"] = "1"
        msg = view()
        self.assertTrue("meeting folders initialized" in msg)

        self.assertTrue(IFacetedNavigable.providedBy(mc_folder))
        self.assertEqual(mc_folder.getProperty(MEETING_CONFIG), cfg_id)
        self.assertTrue("searches_items" in mc_folder.objectIds())
        self.assertTrue(cfg.getItemTypeName() in mc_folder.locally_allowed_types)
        mm_group = "%s_%s" % (cfg_id, MEETINGMANAGERS_GROUP_SUFFIX)
        self.assertTrue("MeetingManager" in dict(mc_folder.get_local_roles())[mm_group])
        from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
        self.assertEqual(ISelectableConstrainTypes(root).getLocallyAllowedTypes(), ["Folder"])
        # the tool reuses the folder instead of creating a new one
        self.assertEqual(self.tool.getPloneMeetingFolder(cfg_id, "pmCreator2"), mc_folder)
        # calling it again is harmless
        view()
        self.assertEqual(mc_folder.getProperty(MEETING_CONFIG), cfg_id)

    def test_post_process_updates_categorized_elements(self):
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        annex = self.addAnnex(item)
        item.categorized_elements.clear()
        self.assertFalse(annex.UID() in item.categorized_elements)
        self.changeUser("siteadmin")
        msg = self.portal.restrictedTraverse("@@import_pm_post_process")()
        self.assertTrue("categorized_elements updated" in msg)
        self.assertTrue(annex.UID() in item.categorized_elements)

    def test_post_process_builds_the_annex_type_icons(self):
        """The import writes the icon of an annex type after the object
           is created, so its listing scale is not built."""
        from plone.namedfile.interfaces import IAvailableSizes
        from zope.annotation.interfaces import IAnnotations
        self.changeUser("siteadmin")
        cfg = self.meetingConfig
        category = cfg.annexes_types.item_annexes.objectValues()[0]
        # what an imported category looks like: no scale built yet
        IAnnotations(category).pop("plone.scale", None)
        self.assertTrue(IAvailableSizes is not None)
        msg = self.portal.restrictedTraverse("@@import_pm_post_process")()
        self.assertTrue("annex type icons built" in msg)
        self.assertTrue("plone.scale" in IAnnotations(category))

    def test_the_meeting_folders_know_their_config(self):
        """The items are imported in these folders, and the tool reads
           the property to know the config an item belongs to."""
        from plonemeeting.core.config import MEETING_CONFIG
        cfg = self.meetingConfig
        cfg_id = cfg.getId()
        self.changeUser("siteadmin")
        root, mc_folder = self._plain_imported_folders("pmCreator2", cfg_id)
        self.assertFalse(mc_folder.hasProperty(MEETING_CONFIG))
        self.assertIsNone(self.tool.getMeetingConfig(mc_folder))

        msg = self.portal.restrictedTraverse("@@import_pm_meeting_folders")()

        self.assertTrue("meeting folders initialized" in msg)
        self.assertEqual(mc_folder.getProperty(MEETING_CONFIG), cfg_id)
        self.assertEqual(self.tool.getMeetingConfig(mc_folder), cfg)

    def test_the_import_does_not_play_the_transitions_of_an_object(self):
        """A transition is an action: the workflow history is the only
           source of the state of an imported object."""
        from plonemeeting.core.migrations.p4top6.import_content import \
            PMImportContent
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        self.changeUser("siteadmin")
        importer = PMImportContent(self.portal, self.request)
        importer.start()
        importer.import_review_state(item, {"review_state": "validated"})
        self.assertEqual(api.content.get_state(item), "itemcreated")

    def test_post_process_gives_back_the_permissions_of_the_state(self):
        """collective.exportimport writes the workflow history after the
           object is created, so the object keeps the permissions of the
           state it was created in, and the catalog keeps that state."""
        permission = "Modify portal content"

        def roles_of(obj):
            return sorted(entry["name"] for entry
                          in obj.rolesOfPermission(permission)
                          if entry["selected"])

        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        self.changeUser("siteadmin")
        expected = roles_of(item)
        self.assertTrue(len(expected) > 1)
        # what an imported object looks like: the permissions of another state
        item.manage_permission(permission, ("Manager", ), acquire=0)
        self.assertEqual(roles_of(item), ["Manager"])

        msg = self.portal.restrictedTraverse("@@import_pm_post_process")()

        self.assertTrue("permissions of their state" in msg)
        self.assertEqual(roles_of(item), expected)
        brain = self.portal.portal_catalog(UID=item.UID())[0]
        self.assertEqual(brain.review_state, api.content.get_state(item))

    def test_the_import_does_not_let_an_advice_recompute_itself(self):
        """The add handler of an advice computes what the import already
           holds, and what it computes can raise: the 4.3 site has
           advices of a group the config no longer asks."""
        from Products.CMFPlone.utils import _createObjectByType
        from plonemeeting.core.migrations.p4top6.import_content import \
            IMPORTING_KEY
        self.changeUser("pmManager")
        item = self.create("MeetingItem")
        self.changeUser("siteadmin")
        fields = {"advice_group": self.vendors_uid, "advice_type": u"positive"}
        cfg = self.meetingConfig
        self.assertFalse(self.vendors_uid in item.adviceIndex)
        self.assertFalse(self.vendors_uid in cfg.power_advisers_groups)
        self.assertRaises(KeyError, _createObjectByType,
                          "meetingadvice", item, "asked", **fields)

        self.request.set(IMPORTING_KEY, True)
        advice = _createObjectByType("meetingadvice", item, "imported", **fields)

        # the handler stopped before it wrote anything of its own
        self.assertIsNone(getattr(advice, "advice_given_history", None))
        # the permissions it computes are the only thing it still does
        self.assertEqual(
            advice.acquiredRolesAreUsedBy(
                "plone.app.contenttypes: Add Image"), "")
        # the import writes the fields after, one event at a time
        from zope.lifecycleevent import modified
        advice.advice_type = u"negative"
        modified(advice)

    def test_the_import_defers_the_annex_cache(self):
        """The cache of a container cannot be built while the annexes of
           the container are still created empty."""
        from plonemeeting.core.migrations.p4top6.import_content import \
            DEFER_CATEGORIZED_KEYS
        from plonemeeting.core.migrations.p4top6.import_content import \
            PMImportContent
        self.changeUser("siteadmin")
        from plonemeeting.core.migrations.p4top6.import_content import \
            SKIP_VALIDATORS_KEY
        keys = DEFER_CATEGORIZED_KEYS + (SKIP_VALIDATORS_KEY, )
        importer = PMImportContent(self.portal, self.request)
        importer.start()
        for key in keys:
            self.assertTrue(self.request.get(key))
        importer.finish()
        for key in keys:
            self.assertFalse(self.request.get(key))


class TestDirectoryImport(PloneMeetingTestCase):
    """The contacts directory already exists when the contacts are
       imported, so its fields are applied on the existing object."""

    def _importer(self):
        from plonemeeting.core.migrations.p4top6.import_content import PMImportContent
        importer = PMImportContent(self.portal, self.request)
        importer.start()
        return importer

    def test_directory_fields_land_on_the_existing_directory(self):
        self.changeUser('siteadmin')
        directory = self.portal.contacts
        position_types = [{"name": u"Bourgmestre", "token": "bourgmestre"},
                          {"name": u"Échevin", "token": "alderman"}]
        item = {"@id": "http://nohost/plone/contacts",
                "@type": "directory",
                "id": "contacts",
                "UID": directory.UID(),
                "position_types": position_types,
                "organization_types": [{"name": u"Service", "token": "srv"}]}
        self._importer().global_dict_hook(item)
        self.assertEqual(directory.position_types, position_types)
        self.assertEqual(directory.organization_types,
                         [{"name": u"Service", "token": "srv"}])
        # a field the export does not carry is left alone
        self.assertTrue(directory.organization_levels)

    def test_missing_directory_is_left_to_the_import(self):
        self.changeUser('siteadmin')
        item = {"@id": "http://nohost/plone/other-contacts",
                "@type": "directory",
                "id": "other-contacts",
                "UID": "nothing",
                "position_types": [{"name": u"X", "token": "x"}]}
        # no exception, and the fields stay in the item so the import
        # creates the directory with them
        res = self._importer().global_dict_hook(item)
        self.assertEqual(res["position_types"], [{"name": u"X", "token": "x"}])


class TestDeferredFields(PloneMeetingTestCase):
    """Fields that point at content which is not imported yet are taken
       out of the item and applied again later."""

    def _schema_names(self, portal_type):
        """Every field name of a type, its behaviors included."""
        fti = getUtility(IDexterityFTI, name=portal_type)
        names = set(getFieldNames(fti.lookupSchema()))
        for behavior_id in fti.behaviors:
            behavior = queryUtility(IBehavior, behavior_id)
            if behavior is not None and behavior.interface is not None:
                names.update(getFieldNames(behavior.interface))
        return names

    def test_deferred_fields_exist(self):
        """A deferred field that no schema declares is data loss: the
           import drops it and nothing puts it back."""
        for portal_type, names in mappings.DEFERRED_FIELDS.items():
            self.assertEqual(set(names) - self._schema_names(portal_type),
                             set(), "on %s" % portal_type)

    def test_config_factory_fields_exist(self):
        """A factory kwarg that createContent() cannot place is set as a
           plain attribute and shadows nothing: the value is lost."""
        from plone.dexterity.content import DexterityContent

        import inspect

        names = self._schema_names("MeetingConfig")
        # createContent() also accepts the named parameters of the
        # Dexterity constructor, "title" among them
        names.update(inspect.signature(DexterityContent.__init__).parameters)
        self.assertEqual(set(mappings.CONFIG_FACTORY_FIELDS) - names, set())
        self.assertTrue(mappings.CONFIG_WF_ADAPTATIONS_FIELD in
                        self._schema_names("MeetingConfig"))
        # every type of the table, the configs included
        for portal_type, fields in mappings.FACTORY_FIELDS.items():
            known = self._schema_names(portal_type)
            known.update(
                inspect.signature(DexterityContent.__init__).parameters)
            self.assertEqual(set(fields) - known, set(),
                             "%s: unknown factory fields" % portal_type)

    def _importer(self):
        from plonemeeting.core.migrations.p4top6.import_content import PMImportContent
        importer = PMImportContent(self.portal, self.request)
        importer.start()
        return importer

    def test_deferred_then_applied(self):
        from plonemeeting.core.migrations.p4top6.import_content import apply_deferred_fields
        from plonemeeting.core.migrations.p4top6.import_content import deferred_store
        self.changeUser('siteadmin')
        vendors = self.portal.contacts[PLONEGROUP_ORG]['vendors']
        self.assertEqual(vendors.groups_in_charge, [])
        item = {"@id": vendors.absolute_url(),
                "@type": "organization",
                "id": "vendors",
                "UID": self.vendors_uid,
                "title": u"Vendors",
                "groups_in_charge": [self.developers_uid],
                # an empty value needs no second pass
                "item_advice_states": []}
        res = self._importer().global_dict_hook(item)
        self.assertTrue("groups_in_charge" not in res)
        self.assertEqual(res["item_advice_states"], [])
        self.assertEqual(deferred_store()[self.vendors_uid],
                         {"groups_in_charge": [self.developers_uid]})

        applied, remaining, missing = apply_deferred_fields(self.request)
        self.assertEqual((applied, remaining, missing), (1, 0, 0))
        self.assertEqual(vendors.groups_in_charge, [self.developers_uid])
        self.assertEqual(deferred_store(), {})

    def test_a_deferred_choice_keeps_its_token(self):
        """A deferred value leaves the data before the hook that gives a
           Choice its token reads it."""
        from plonemeeting.core.migrations.p4top6.import_content import \
            apply_deferred_fields
        from plonemeeting.core.migrations.p4top6.import_content import \
            deferred_store
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        self.changeUser("siteadmin")
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "UID": item.UID(),
                "preferred_meeting": {"title": u"No preference",
                                      "token": "whatever"}}
        res = self._importer().global_dict_hook(data)
        self.assertTrue("preferred_meeting" not in res)

        applied, remaining, missing = apply_deferred_fields(self.request)

        self.assertEqual((applied, remaining, missing), (1, 0, 0))
        self.assertEqual(item.preferred_meeting, "whatever")
        self.assertEqual(deferred_store(), {})

    def test_value_that_still_does_not_validate_waits(self):
        from plonemeeting.core.migrations.p4top6.import_content import apply_deferred_fields
        from plonemeeting.core.migrations.p4top6.import_content import deferred_store
        self.changeUser('siteadmin')
        item = {"@id": self.portal.contacts.absolute_url(),
                "@type": "organization",
                "id": "vendors",
                "UID": self.vendors_uid,
                "groups_in_charge": ["a-uid-that-does-not-exist"]}
        self._importer().global_dict_hook(item)
        applied, remaining, missing = apply_deferred_fields(self.request)
        self.assertEqual((applied, remaining, missing), (0, 1, 0))
        self.assertTrue(self.vendors_uid in deferred_store())

    def test_item_types_share_one_entry(self):
        """The item types are cloned per config, the table has one
           "MeetingItem" entry for all of them."""
        self.changeUser('siteadmin')
        importer = self._importer()
        item = {"@id": "http://nohost/plone/an-item",
                "@type": self.meetingConfig.getItemTypeName(),
                "id": "an-item",
                "UID": "the-uid-of-an-item",
                "preferred_meeting": "the-uid-of-a-meeting"}
        res = importer.global_dict_hook(item)
        self.assertTrue("preferred_meeting" not in res)
        from plonemeeting.core.migrations.p4top6.import_content import deferred_store
        self.assertEqual(deferred_store()["the-uid-of-an-item"],
                         {"preferred_meeting": "the-uid-of-a-meeting"})

    def test_object_that_was_not_imported_is_reported(self):
        from plonemeeting.core.migrations.p4top6.import_content import apply_deferred_fields
        from plonemeeting.core.migrations.p4top6.import_content import deferred_store
        self.changeUser('siteadmin')
        deferred_store(create=True)["unknown-uid"] = {"groups_in_charge": []}
        applied, remaining, missing = apply_deferred_fields(self.request)
        self.assertEqual((applied, remaining, missing), (0, 0, 1))


class TestImportRegistry(PloneMeetingTestCase):
    """@@import_pm_registry writes the records the export carries."""

    def test_records_are_set_and_unknown_ones_skipped(self):
        from plone import api

        import json
        import os
        import tempfile

        self.changeUser('siteadmin')
        records = [{"name": "plone.email_from_name", "value": u"iA.Delib"},
                   {"name": "plonemeeting.no.such.record", "value": 1}]
        handle, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w") as dump:
            json.dump(records, dump)
        try:
            self.request.form["path"] = path
            view = self.portal.restrictedTraverse("@@import_pm_registry")
            msg = view()
        finally:
            os.remove(path)
        self.assertEqual(msg, "registry: 1 of 2 records set")
        self.assertEqual(
            api.portal.get_registry_record("plone.email_from_name"),
            u"iA.Delib")


class TestContainers(PloneMeetingTestCase):
    """Where an imported object lands."""

    def _importer(self):
        from plonemeeting.core.migrations.p4top6.import_content import PMImportContent
        importer = PMImportContent(self.portal, self.request)
        importer.start()
        return importer

    def test_the_tool_is_the_container_of_a_config(self):
        """portal_plonemeeting is not imported content: its UID is the
           one of the new site, so the UID of the export finds nothing
           and the stock import creates a Folder beside it."""
        self.changeUser('siteadmin')
        item = {"@id": "http://nohost/plone/portal_plonemeeting/new-cfg",
                "@type": "MeetingConfig",
                "id": "new-cfg",
                "parent": {"@id": "http://nohost/plone/portal_plonemeeting",
                           "@type": "ToolPloneMeeting",
                           "UID": "the-uid-of-the-43-tool"}}
        self.assertEqual(self._importer().get_parent_as_container(item),
                         self.tool)

    def test_a_missing_container_is_not_invented(self):
        self.changeUser('siteadmin')
        item = {"@id": "http://nohost/plone/gone/item",
                "@type": "Folder",
                "id": "item",
                "parent": {"@id": "http://nohost/plone/gone",
                           "@type": "Folder",
                           "UID": "no-such-uid"}}
        self.assertIsNone(self._importer().get_parent_as_container(item))
        self.assertTrue("gone" not in self.portal.objectIds())

    def test_a_language_the_site_does_not_offer_is_dropped(self):
        """A 4.3 site that was never multilingual still holds "fr-be",
           "en" and the neutral empty token."""
        self.changeUser('siteadmin')
        importer = self._importer()
        folder = api.content.create(
            container=self.portal, type="Folder", id="a-folder",
            title=u"A folder")
        item = {"@id": folder.absolute_url(),
                "@type": "Folder",
                "id": "a-folder",
                "language": {"title": "French (Belgium)", "token": "fr-be"}}
        importer.global_obj_hook_before_deserializing(folder, item)
        self.assertTrue("language" not in item)

    def test_an_empty_value_is_not_imported(self):
        """The 4.3 site has items with no category and no group in
           charge; an empty value would run the validator of the
           field."""
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "category": {"title": None, "token": ""},
                "groupsInCharge": [],
                "proposingGroup": {"title": u"Developers",
                                   "token": self.developers_uid}}
        self.changeUser("siteadmin")
        importer = self._importer()
        # the item keys are the Archetypes ones until global_dict_hook
        data = importer.global_dict_hook(data)
        importer.global_obj_hook_before_deserializing(item, data)
        self.assertTrue("category" not in data)
        self.assertTrue("groups_in_charge" not in data)
        self.assertEqual(data["proposing_group"], self.developers_uid)

    def test_a_privacy_the_config_dropped_falls_back(self):
        """An item keeps a privacy its MeetingConfig does not offer any
           more. A heading privacy is a sub-kind of the base one."""
        cfg = self.meetingConfig
        self.changeUser("siteadmin")
        cfg.selectable_privacies = ("public", "secret")
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "privacy": {"title": u"Closed door (heading)",
                            "token": "secret_heading"}}
        self.changeUser("siteadmin")
        self._importer().global_obj_hook_before_deserializing(item, data)
        self.assertEqual(data["privacy"], "secret")
        # a value the config offers is left alone
        data["privacy"] = {"title": u"Closed door", "token": "secret"}
        self._importer().global_obj_hook_before_deserializing(item, data)
        self.assertEqual(data["privacy"], "secret")

    def test_a_category_the_config_does_not_have_leaves_the_item(self):
        """A site that ran for ten years holds items whose category was
           deleted, or belongs to another MeetingConfig. An item with no
           category is a smaller loss than no item at all."""
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "category": {"title": u"Informatique",
                             "token": "informatique"}}
        self.changeUser("siteadmin")
        self._importer().global_obj_hook_before_deserializing(item, data)
        self.assertFalse("category" in data)
        # a category the config has is left alone
        category_id = self.meetingConfig.getCategories(
            onlySelectable=False)[0].getId()
        data["category"] = {"title": u"Whatever", "token": category_id}
        self._importer().global_obj_hook_before_deserializing(item, data)
        self.assertEqual(data["category"], category_id)

    def test_a_type_the_new_site_does_not_have_leaves_the_constraints(self):
        """A 4.3 folder allows MeetingFile or Large Plone Folder.
           ISelectableConstrainTypes refuses the whole list when one id
           is unknown."""
        self.changeUser("siteadmin")
        data = {"@id": "http://nohost/plone/a-folder",
                "@type": "Folder",
                "id": "a-folder",
                "exportimport.constrains": {
                    "locally_allowed_types": ["Folder", "MeetingFile"],
                    "immediately_addable_types": ["Large Plone Folder"]}}
        res = self._importer().global_dict_hook(data)
        constrains = res["exportimport.constrains"]
        self.assertEqual(constrains["locally_allowed_types"], ["Folder"])
        self.assertEqual(constrains["immediately_addable_types"], [])

    def test_a_tag_the_config_dropped_leaves_the_item(self):
        """An item keeps a tag the MeetingConfig does not offer any
           more. The other tags of the item stay."""
        cfg = self.meetingConfig
        self.changeUser("siteadmin")
        cfg.all_item_tags = u"Tag1\nTag2"
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "itemTags": [{"title": u"Tag1", "token": "Tag1"},
                             {"title": u"Test", "token": "Test"}]}
        self.changeUser("siteadmin")
        importer = self._importer()
        data = importer.global_dict_hook(data)
        importer.global_obj_hook_before_deserializing(item, data)
        self.assertEqual(data["item_tags"], ["Tag1"])
        # nothing the config offers means no value at all
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "itemTags": [{"title": u"Test", "token": "Test"}]}
        data = importer.global_dict_hook(data)
        importer.global_obj_hook_before_deserializing(item, data)
        self.assertTrue("item_tags" not in data)

    def test_a_pod_template_gets_the_md5_of_its_file(self):
        """The 4.3 site has templates whose md5 was never computed, and
           the fields are required on the new schema."""
        self.changeUser("siteadmin")
        cfg = self.meetingConfig
        template = [pod for pod in cfg.podtemplates.objectValues()
                    if pod.portal_type == "ConfigurablePODTemplate"][0]
        data = {"@id": template.absolute_url(),
                "@type": template.portal_type,
                "id": template.getId(),
                "initial_md5": None,
                "style_modification_md5": None}
        self._importer().global_obj_hook_before_deserializing(template, data)
        self.assertEqual(data["initial_md5"], template.current_md5)
        self.assertEqual(data["style_modification_md5"], template.current_md5)
        self.assertTrue(data["initial_md5"])
        # a value the export carries is kept
        data = {"@id": template.absolute_url(),
                "@type": template.portal_type,
                "id": template.getId(),
                "initial_md5": u"an-md5"}
        self._importer().global_obj_hook_before_deserializing(template, data)
        self.assertEqual(data["initial_md5"], u"an-md5")

    def test_a_rich_text_that_was_never_set_is_dropped(self):
        """plone.restapi unescapes the data of a rich text without a
           check, and an AT TextField that was never set has none."""
        self.changeUser("pmCreator1")
        item = self.create("MeetingItem")
        data = {"@id": item.absolute_url(),
                "@type": item.portal_type,
                "id": item.getId(),
                "description": {"content-type": "text/html", "data": None},
                "decision": {"content-type": "text/html", "data": None},
                "observations": None,
                "motivation": {"content-type": "text/html",
                               "data": u"<p>Motivation</p>"}}
        self.changeUser("siteadmin")
        self._importer().global_obj_hook_before_deserializing(item, data)
        self.assertTrue("decision" not in data)
        # the export writes a plain null too
        self.assertTrue("observations" not in data)
        self.assertEqual(data["motivation"]["data"], u"<p>Motivation</p>")

    def test_dublin_core_text_fields_are_unwrapped(self):
        """Every Archetypes type of the 4.3 site exports "description"
           and "rights" as a TextField dict."""
        self.changeUser('siteadmin')
        item = {"@id": "http://nohost/plone/a-folder",
                "@type": "Folder",
                "id": "a-folder",
                "description": {"content-type": "text/plain",
                                "data": u"Une description"},
                "rights": {"content-type": "text/plain", "data": u""}}
        res = self._importer().global_dict_hook(item)
        self.assertEqual(res["description"], u"Une description")
        self.assertEqual(res["rights"], u"")
