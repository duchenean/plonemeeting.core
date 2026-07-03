# -*- coding: utf-8 -*-
"""Unit tests for the P4 -> P6 collective.exportimport import hooks.

Pure dict-transform tests plus mapping invariants against the DX
schemas — no Plone layer needed.
"""

import unittest

from zope.schema import getFieldNames

from plonemeeting.core.content.meetingconfig import IMeetingConfig
from plonemeeting.core.content.meetingitem import IMeetingItem
from plonemeeting.core.migrations.p4top6 import mappings
from plonemeeting.core.migrations.p4top6.import_content import _remap_row_keys
from plonemeeting.core.migrations.p4top6.import_content import _rename_keys
from plonemeeting.core.migrations.p4top6.import_content import _unwrap_plain_text


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
