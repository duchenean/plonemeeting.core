# -*- coding: utf-8 -*-

# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from __future__ import absolute_import, print_function

from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plonemeeting.core.interfaces import IMeetingItem


# Port of the AT widget ``condition=`` expressions that lived on the legacy
# MeetingItem schema. Each entry maps a field name to a callable
# ``(context, cfg, is_item) -> bool`` returning True when the field should be
# rendered. ``is_item`` distinguishes Edit-form context (a real MeetingItem)
# from Add-form context (the parent folder, before the item exists).
#
# Edit branch: call the existing ``MeetingItem.show*()`` / ``attribute_is_used()``
# helpers on the item — they encapsulate per-item state, permissions, and
# acquisition of the active MeetingConfig.
#
# Add branch: best-effort fallback against ``cfg`` only — typically just
# ``attribute_is_used`` on ``cfg.used_item_attributes``, with cfg-derived checks
# for the few helpers that don't need item state (e.g. cfg.use_advices).
# Conditions that fundamentally need item state (assembly fields, MM-only
# notes, follow-ups, etc.) return False on Add — they will appear after first
# save through the Edit form.


def _is_in_tool(ctx):
    """True if ``ctx`` lives inside ``portal_plonemeeting`` (item template
    / recurring item slot)."""
    abs_url = getattr(ctx, 'absolute_url', None)
    if abs_url is None:
        return False
    try:
        return 'portal_plonemeeting' in abs_url()
    except Exception:
        return False


def _used(name):
    """Build a callable that checks ``name in cfg.used_item_attributes``."""
    def _check(ctx, cfg, is_item):
        return name in (cfg.used_item_attributes or [])
    return _check


def _emergency_add_fallback(cfg):
    if 'emergency' in (cfg.used_item_attributes or []):
        return True
    return any('accepted_out_of_meeting' in wfa
               for wfa in (cfg.workflow_adaptations or []))


def _oral_question_add_fallback(cfg):
    if 'oral_question' not in (cfg.used_item_attributes or []):
        return False
    tool = api.portal.get_tool('portal_plonemeeting')
    return tool.isManager(cfg)


def _acceptable_add_fallback(cfg):
    return any(wfa.startswith('accepted_out_of_meeting')
               for wfa in (cfg.workflow_adaptations or []))


def _completeness(ctx, cfg, is_item):
    if 'completeness' not in (cfg.used_item_attributes or []):
        return False
    if not is_item:
        return False
    adapted = ctx.adapted()
    return adapted.mayEvaluateCompleteness() or adapted.mayAskCompletenessEvalAgain()


def _poll_type(ctx, cfg, is_item):
    if is_item:
        return ((ctx.attribute_is_used('poll_type') or ctx.isVotesEnabled())
                and ctx.adapted().mayChangePollType())
    return ('poll_type' in (cfg.used_item_attributes or [])
            or cfg.use_votes)


_FIELD_VISIBILITY = {
    # ---- attribute_is_used: simple cfg.used_item_attributes membership ----
    'detailed_description': _used('detailed_description'),
    'proposing_group_with_group_in_charge': _used('proposing_group_with_group_in_charge'),
    'proposing_group': lambda ctx, cfg, is_item: (
        'proposing_group_with_group_in_charge' not in (cfg.used_item_attributes or [])),
    'associated_groups': _used('associated_groups'),
    'category': _used('category'),
    'classifier': _used('classifier'),
    'item_tags': _used('item_tags'),
    'item_keywords': _used('item_keywords'),
    'emergency_motivation': _used('emergency_motivation'),
    'motivation': _used('motivation'),
    'decision_suite': _used('decision_suite'),
    'decision_end': _used('decision_end'),
    'votes_result': _used('votes_result'),
    'item_initiator': _used('item_initiator'),
    'internal_notes': _used('internal_notes'),
    'marginal_notes': _used('marginal_notes'),
    'copy_groups': _used('copy_groups'),
    'restricted_copy_groups': _used('restricted_copy_groups'),
    'poll_type_observations': _used('poll_type_observations'),
    'committee_observations': _used('committee_observations'),
    'committee_transcript': _used('committee_transcript'),
    'send_to_authority': _used('send_to_authority'),
    'privacy': _used('privacy'),
    'taken_over_by': _used('taken_over_by'),

    # ---- clonable-to-other-MCs (each gated by attribute_is_used) ----
    'other_meeting_configs_clonable_to_emergency':
        _used('other_meeting_configs_clonable_to_emergency'),
    'other_meeting_configs_clonable_to_privacy':
        _used('other_meeting_configs_clonable_to_privacy'),
    'other_meeting_configs_clonable_to_field_title':
        _used('other_meeting_configs_clonable_to_field_title'),
    'other_meeting_configs_clonable_to_field_description':
        _used('other_meeting_configs_clonable_to_field_description'),
    'other_meeting_configs_clonable_to_field_detailed_description':
        _used('other_meeting_configs_clonable_to_field_detailed_description'),
    'other_meeting_configs_clonable_to_field_motivation':
        _used('other_meeting_configs_clonable_to_field_motivation'),
    'other_meeting_configs_clonable_to_field_decision':
        _used('other_meeting_configs_clonable_to_field_decision'),
    'other_meeting_configs_clonable_to_field_decision_suite':
        _used('other_meeting_configs_clonable_to_field_decision_suite'),
    'other_meeting_configs_clonable_to_field_decision_end':
        _used('other_meeting_configs_clonable_to_field_decision_end'),

    # ---- compound: attribute_is_used + isDefinedInTool ----
    'manually_linked_items': lambda ctx, cfg, is_item: (
        'manually_linked_items' in (cfg.used_item_attributes or [])
        and not _is_in_tool(ctx)),
    'meeting_deadline_date': lambda ctx, cfg, is_item: (
        'meeting_deadline_date' in (cfg.used_item_attributes or [])
        and not _is_in_tool(ctx)),
    'preferred_meeting': lambda ctx, cfg, is_item: not _is_in_tool(ctx),
    'meeting_transition_inserting_me': lambda ctx, cfg, is_item: (
        _is_in_tool(ctx)
        and getattr(ctx, 'portal_type', '').startswith('MeetingItemRecurring')),
    'template_using_groups': lambda ctx, cfg, is_item: (
        _is_in_tool(ctx)
        and getattr(ctx, 'portal_type', '').startswith('MeetingItemTemplate')),

    # ---- show_* helpers (use real helper on item, fallback on Add) ----
    'budget_infos': lambda ctx, cfg, is_item: (
        ctx.show_budget_infos() if is_item
        else 'budget_infos' in (cfg.used_item_attributes or [])),
    'budget_related': lambda ctx, cfg, is_item: (
        ctx.show_budget_infos() if is_item
        else 'budget_infos' in (cfg.used_item_attributes or [])),
    'groups_in_charge': lambda ctx, cfg, is_item: (
        ctx.show_groups_in_charge() if is_item
        else 'groups_in_charge' in (cfg.used_item_attributes or [])),
    'committees': lambda ctx, cfg, is_item: (
        ctx.show_committees() if is_item
        else ('committees' in (cfg.used_item_attributes or [])
              or 'committees' in (cfg.used_meeting_attributes or []))),
    'list_type': lambda ctx, cfg, is_item: (
        ctx.adapted().mayChangeListType() if is_item else False),
    'emergency': lambda ctx, cfg, is_item: (
        ctx.showEmergency() if is_item else _emergency_add_fallback(cfg)),
    'optional_advisers': lambda ctx, cfg, is_item: (
        ctx.showOptionalAdvisers() if is_item else cfg.use_advices),
    'groups_in_charge_notes': lambda ctx, cfg, is_item: (
        ctx.adapted().show_field('groups_in_charge_notes') if is_item else False),
    'needed_follow_up': lambda ctx, cfg, is_item: (
        ctx.adapted().show_field('needed_follow_up') if is_item else False),
    'provided_follow_up': lambda ctx, cfg, is_item: (
        ctx.adapted().show_field('provided_follow_up') if is_item else False),
    'in_and_out_moves': lambda ctx, cfg, is_item: (
        ctx.showMeetingManagerReservedField('in_and_out_moves') if is_item else False),
    'notes': lambda ctx, cfg, is_item: (
        ctx.showMeetingManagerReservedField('notes') if is_item else False),
    'meeting_managers_notes': lambda ctx, cfg, is_item: (
        ctx.showMeetingManagerReservedField('meeting_managers_notes') if is_item else False),
    'meeting_managers_notes_suite': lambda ctx, cfg, is_item: (
        ctx.showMeetingManagerReservedField('meeting_managers_notes_suite') if is_item else False),
    'meeting_managers_notes_end': lambda ctx, cfg, is_item: (
        ctx.showMeetingManagerReservedField('meeting_managers_notes_end') if is_item else False),
    'text_check_list': lambda ctx, cfg, is_item: (
        ctx.showMeetingManagerReservedField('text_check_list') if is_item else False),
    'oral_question': lambda ctx, cfg, is_item: (
        ctx.showOralQuestion() if is_item else _oral_question_add_fallback(cfg)),
    'to_discuss': lambda ctx, cfg, is_item: (
        ctx.showToDiscuss() if is_item
        else 'to_discuss' in (cfg.used_item_attributes or [])),
    'item_assembly': lambda ctx, cfg, is_item: (
        ctx.is_assembly_field_used('item_assembly') if is_item else False),
    'item_assembly_excused': lambda ctx, cfg, is_item: (
        ctx.is_assembly_field_used('item_assembly_excused') if is_item else False),
    'item_assembly_absents': lambda ctx, cfg, is_item: (
        ctx.is_assembly_field_used('item_assembly_absents') if is_item else False),
    'item_assembly_guests': lambda ctx, cfg, is_item: (
        ctx.is_assembly_field_used('item_assembly_guests') if is_item else False),
    'item_signatures': lambda ctx, cfg, is_item: (
        ctx.is_assembly_field_used('item_signatures') if is_item else False),
    'votes_observations': lambda ctx, cfg, is_item: (
        ctx.adapted().show_votesObservations() if is_item
        else 'votes_observations' in (cfg.used_item_attributes or [])),
    'other_meeting_configs_clonable_to': lambda ctx, cfg, is_item: (
        ctx.showClonableToOtherMCs() if is_item
        else bool(cfg.meeting_configs_to_clone_to)),
    'is_acceptable_out_of_meeting': lambda ctx, cfg, is_item: (
        ctx.showIsAcceptableOutOfMeeting() if is_item
        else _acceptable_add_fallback(cfg)),
    'poll_type': _poll_type,
    'completeness': _completeness,
    'item_is_signed': lambda ctx, cfg, is_item: (
        ctx.showItemIsSigned() if is_item else False),
    'observations': lambda ctx, cfg, is_item: (
        ctx.adapted().showObservations() if is_item
        else 'observations' in (cfg.used_item_attributes or [])),
}


class MeetingItemFormMixin(object):
    """Shared field-visibility logic for the MeetingItem Add and Edit forms.

    Walks ``[self] + self.groups`` (default fieldset + named fieldsets) and
    omits any field whose entry in ``_FIELD_VISIBILITY`` returns False. Fields
    not in the table (item_number, item_reference, description, decision)
    are unconditional and always render.
    """

    def _compute_hidden_fields(self):
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self.context)
        if cfg is None:
            return set()
        is_item = IMeetingItem.providedBy(self.context)
        hidden = set()
        for field_name, predicate in _FIELD_VISIBILITY.items():
            try:
                if not predicate(self.context, cfg, is_item):
                    hidden.add(field_name)
            except Exception:
                # Defensive: a misbehaving helper shouldn't crash the form.
                # Log via Plone's standard mechanism would be nice but a
                # plain print is enough during the migration phase.
                pass
        return hidden

    def _apply_field_visibility(self):
        hidden = self._compute_hidden_fields()
        if not hidden:
            return
        for group in [self] + list(getattr(self, 'groups', []) or []):
            for field_name in list(group.fields):
                if field_name in hidden:
                    group.fields = group.fields.omit(field_name)


class MeetingItemEditForm(MeetingItemFormMixin, DefaultEditForm):

    def updateFields(self):
        super(MeetingItemEditForm, self).updateFields()
        self._apply_field_visibility()


class MeetingItemAddForm(MeetingItemFormMixin, DefaultAddForm):

    def updateFields(self):
        super(MeetingItemAddForm, self).updateFields()
        self._apply_field_visibility()


class MeetingItemAddView(DefaultAddView):

    form = MeetingItemAddForm
