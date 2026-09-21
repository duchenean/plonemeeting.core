# -*- coding: utf-8 -*-
"""Tests for the P4 -> P6 collective.exportimport hooks.

Dict-transform tests and mapping invariants against the DX schemas
(no Plone layer), plus extra-state round-trips on real content.
"""

import unittest

from zope.schema import getFieldNames

from plonemeeting.core.content.meetingconfig import IMeetingConfig
from plonemeeting.core.content.meetingitem import IMeetingItem
from plonemeeting.core.migrations.p4top6 import mappings
from plonemeeting.core.migrations.p4top6.import_content import _remap_row_keys
from plonemeeting.core.migrations.p4top6.import_content import _rename_keys
from plonemeeting.core.migrations.p4top6.import_content import _unwrap_plain_text
from plonemeeting.core.tests.PloneMeetingTestCase import PloneMeetingTestCase


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

    def test_row_key_map_grids_exist(self):
        self.assertEqual(
            set(mappings.ROW_KEY_MAPS) - set(getFieldNames(IMeetingConfig)),
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
        import json
        from plonemeeting.core.migrations.p4top6 import extra_state
        return extra_state.decode(json.loads(json.dumps(extra_state.encode(value))))

    def test_scalars_and_text(self):
        for value in (None, True, 3, 2.5, u"héhé"):
            self.assertEqual(self._round_trip(value), value)
        # py2 utf-8 bytes become text
        self.assertEqual(self._round_trip(u"héhé".encode("utf-8")), u"héhé")

    def test_dates(self):
        import datetime
        from DateTime import DateTime
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
