# -*- coding: utf-8 -*-
#
# File: testForms.py
#
# GNU General Public License (GPL)
#

from __future__ import absolute_import, print_function

from plonemeeting.core.browser.meetingitem import _FIELD_VISIBILITY
from plonemeeting.core.browser.meetingitem import MeetingItemAddForm
from plonemeeting.core.browser.meetingitem import MeetingItemEditForm
from plonemeeting.core.tests.PloneMeetingTestCase import PloneMeetingTestCase
from zope.i18n import translate

import unittest


class testForms(PloneMeetingTestCase):
    """Tests for the DX MeetingItem Add/Edit forms — port of the AT
    visibility helpers (``attribute_is_used``, ``show_*``)."""

    def _make_form(self, FormCls, context):
        """Instantiate the form, wire the FTI, and run updateFields()."""
        form = FormCls(context, self.request)
        # Mimic plone.dexterity.browser.add.DefaultAddView for AddForm
        if FormCls is MeetingItemAddForm:
            from plone.dexterity.interfaces import IDexterityFTI
            from zope.component import getUtility
            portal_type = 'MeetingItem{0}'.format(self.meetingConfig.short_name)
            form.portal_type = portal_type
            form.ti = getUtility(IDexterityFTI, name=portal_type)
        form.update()
        return form

    def _visible_field_names(self, form):
        """Return the union of visible field names across the default
        fieldset and all named groups."""
        names = set(form.fields.keys())
        for group in getattr(form, 'groups', []) or []:
            names.update(group.fields.keys())
        return names

    def _visible_field_titles(self, form):
        """Return translated titles for every visible widget across all groups."""
        titles = []
        for widget in form.widgets.values():
            titles.append(translate(widget.label, context=self.request))
        for group in getattr(form, 'groups', []) or []:
            for widget in group.widgets.values():
                titles.append(translate(widget.label, context=self.request))
        return titles

    def test_pm_AddForm_renders_fieldsets(self):
        """The Add form should expose the named fieldsets we declared
        (proposal, scheduling, decision, ...)."""
        self.changeUser('pmCreator1')
        pmFolder = self.getMeetingFolder()
        form = self._make_form(MeetingItemAddForm, pmFolder)
        group_names = {g.__name__ for g in (form.groups or [])}
        # Only assert the ones that won't be entirely empty under the
        # default test config — proposal at minimum should exist.
        self.assertIn('proposal', group_names)
        self.assertIn('decision', group_names)

    def test_pm_AddForm_hides_unused_attributes(self):
        """With ``detailed_description`` not in cfg.used_item_attributes,
        the field should not be rendered on the Add form."""
        cfg = self.meetingConfig
        cfg.used_item_attributes = [
            attr for attr in cfg.used_item_attributes
            if attr != 'detailed_description'
        ]
        self.changeUser('pmCreator1')
        pmFolder = self.getMeetingFolder()
        form = self._make_form(MeetingItemAddForm, pmFolder)
        visible = self._visible_field_names(form)
        self.assertNotIn('detailed_description', visible)
        # description (no condition) is always present
        self.assertIn('description', visible)

    def test_pm_AddForm_shows_used_attributes(self):
        """When an attribute is added to cfg.used_item_attributes, the
        corresponding field becomes visible on the Add form."""
        cfg = self.meetingConfig
        cfg.used_item_attributes = list(set(
            list(cfg.used_item_attributes) + ['detailed_description', 'category']
        ))
        self.changeUser('pmCreator1')
        pmFolder = self.getMeetingFolder()
        form = self._make_form(MeetingItemAddForm, pmFolder)
        visible = self._visible_field_names(form)
        self.assertIn('detailed_description', visible)
        self.assertIn('category', visible)

    def test_pm_AddForm_no_duplicate_labels(self):
        """Regression — when the clone-to-other-MC fields are NOT in
        ``cfg.used_item_attributes``, none of them should render and the
        ``other_meeting_configs_clonable_to_field_*`` clones (which share
        i18n msgids with the main ``description`` / ``motivation`` /
        ``decision*`` fields) should not produce duplicate visible labels."""
        cfg = self.meetingConfig
        # Ensure no clonable-to-other-MC fields are enabled
        cfg.used_item_attributes = [
            attr for attr in cfg.used_item_attributes
            if not attr.startswith('other_meeting_configs_clonable_to_field_')
        ]
        self.changeUser('pmCreator1')
        pmFolder = self.getMeetingFolder()
        form = self._make_form(MeetingItemAddForm, pmFolder)
        titles = [t for t in self._visible_field_titles(form) if t]
        # No translated label should appear twice.
        seen = {}
        for t in titles:
            seen[t] = seen.get(t, 0) + 1
        duplicates = [t for t, n in seen.items() if n > 1]
        self.assertEqual(duplicates, [],
                         "Duplicate field labels: {0}".format(duplicates))

    def test_pm_FieldVisibilityTable_covers_all_AT_conditions(self):
        """Every field declared with an 'AT condition:' comment in
        content/meetingitem.py should have an entry in _FIELD_VISIBILITY."""
        import re
        from plonemeeting.core.content import meetingitem as mi_module
        with open(mi_module.__file__.replace('.pyc', '.py'), 'r') as f:
            src = f.read()
        # match: "# AT condition: ..." then non-blank lines then "name = (RichText|schema.)"
        pattern = re.compile(
            r"# AT condition:[^\n]*\n(?:[^\n]*\n){0,4}?\s*([a-z_][a-z0-9_]*)\s*=\s*"
            r"(?:RichText|schema\.)",
            re.MULTILINE,
        )
        conditional_fields = set(pattern.findall(src))
        # description has 'AT condition: always shown' which is unconditional
        conditional_fields.discard('description')
        missing = conditional_fields - set(_FIELD_VISIBILITY.keys())
        self.assertEqual(
            missing, set(),
            "Fields with AT conditions missing from _FIELD_VISIBILITY: {0}".format(
                sorted(missing)))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testForms, prefix='test_pm_'))
    return suite
