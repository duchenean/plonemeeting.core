# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#
"""DX MeetingItem schema declaration (B.2.0).

Foundational schema declaration mirroring the Archetypes ``MeetingItem``
field set defined in ``Products/PloneMeeting/MeetingItem.py``. Every AT
field is reproduced under its snake_case DX name. Per-field permissions
(read/write) and the original AT widget ``condition=`` expressions are
preserved verbatim — the latter live in field descriptions for now and
will be migrated to DX form-side ``form.mode`` directives or template
guards in subsequent phases.

Scope of this module:

* Schema interface ``IMeetingItem`` with the 72 fields.
* ``MeetingItemSchemaPolicy`` for the FTI ``schema_policy`` lookup.
* Skeleton ``MeetingItem(Container)`` class — bridging shims (``getField``,
  ``processForm``, ``validate``) and business-method porting are deferred
  to B.2.1+.

The AT class in ``Products/PloneMeeting/MeetingItem.py`` remains the
active implementation until B.2.1 swaps the FTI to Dexterity.

See ``MIGRATION_SUMMARY_MEETINGITEM.md`` at the package root for the
full punch list.
"""

from AccessControl import ClassSecurityInfo
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from Products.PloneMeeting.config import ITEM_NO_PREFERRED_MEETING_VALUE
from Products.PloneMeeting.config import PMMessageFactory as _
from Products.PloneMeeting.config import ReadBudgetInfos
from Products.PloneMeeting.config import WriteBudgetInfos
from Products.PloneMeeting.config import WriteCommitteeFields
from Products.PloneMeeting.config import WriteDecision
from Products.PloneMeeting.config import WriteInternalNotes
from Products.PloneMeeting.config import WriteItemMeetingManagerFields
from Products.PloneMeeting.config import WriteMarginalNotes
from Products.PloneMeeting.interfaces import IMeetingItem as IMeetingItemMarker
from zope import schema
from zope.interface import implements


READ_DECISION = 'PloneMeeting: Read decision'
READ_OBSERVATIONS = 'PloneMeeting: Read item observations'


class IMeetingItem(IMeetingItemMarker):
    """Schema for MeetingItem, migrated from Archetypes OrderedBaseFolder.

    Field declaration order matches the AT schema in ``MeetingItem.py``
    (``schema = Schema((...))``). Per-field ``form.read_permission`` /
    ``form.write_permission`` directives reproduce the AT
    ``read_permission`` / ``write_permission`` arguments.

    AT widget ``condition=`` expressions (``here.attribute_is_used(...)``,
    ``here.adapted().show_field(...)``, etc.) cannot be expressed at
    schema-declaration time on Dexterity. They are preserved as a comment
    above each affected field; the equivalent runtime visibility logic
    will be ported into a form / view layer in B.2.x.
    """

    # ---- default fieldset ----

    item_number = schema.Int(
        title=_(u'PloneMeeting_label_itemNumber', default=u'Itemnumber'),
        required=False,
    )
    form.mode(item_number='hidden')

    item_reference = schema.TextLine(
        title=_(u'PloneMeeting_label_itemReference', default=u'Itemreference'),
        required=False,
    )
    form.mode(item_reference='hidden')

    # AT condition: always shown (no condition).
    description = RichText(
        title=_(u'PloneMeeting_label_itemDescription', default=u'Description'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('detailedDescription')
    detailed_description = RichText(
        title=_(u'PloneMeeting_label_detailedDescription', default=u'Detaileddescription'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.show_budget_infos()
    form.read_permission(budget_related=ReadBudgetInfos)
    form.write_permission(budget_related=WriteBudgetInfos)
    budget_related = schema.Bool(
        title=_(u'PloneMeeting_label_budgetRelated', default=u'Budgetrelated'),
        description=_(u'item_budget_related_descr', default=u'BudgetRelated'),
        required=False,
        default=False,
    )

    # AT condition: python: here.show_budget_infos()
    # AT default_method: getDefaultBudgetInfo (B.2.x: wire as defaultFactory).
    form.read_permission(budget_infos=ReadBudgetInfos)
    form.write_permission(budget_infos=WriteBudgetInfos)
    budget_infos = RichText(
        title=_(u'PloneMeeting_label_budgetInfos', default=u'Budgetinfos'),
        description=_(u'item_budgetinfos_descr', default=u'BudgetInfos'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: not here.attribute_is_used('proposingGroupWithGroupInCharge')
    proposing_group = schema.Choice(
        title=_(u'PloneMeeting_label_proposingGroup', default=u'Proposinggroup'),
        vocabulary=u'Products.PloneMeeting.vocabularies.userproposinggroupsvocabulary',
        required=False,
    )

    # AT condition: here.attribute_is_used('proposingGroupWithGroupInCharge')
    proposing_group_with_group_in_charge = schema.Choice(
        title=_(u'PloneMeeting_label_proposingGroupWithGroupInCharge',
                default=u'Proposinggroupwithgroupincharge'),
        vocabulary=u'Products.PloneMeeting.vocabularies.userproposinggroupswithgroupsinchargevocabulary',
        required=False,
    )

    # AT condition: python: here.show_groups_in_charge()
    groups_in_charge = schema.List(
        title=_(u'PloneMeeting_label_groupsInCharge', default=u'Groupsincharge'),
        description=_(u'item_groups_in_charge_descr', default=u'Groupsincharge'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.itemgroupsinchargevocabulary'),
        required=False,
        default=[],
    )

    # AT condition: python: here.attribute_is_used('associatedGroups')
    associated_groups = schema.List(
        title=_(u'PloneMeeting_label_associatedGroups', default=u'Associatedgroups'),
        description=_(u'associated_group_item_descr', default=u'Associatedgroups'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.itemassociatedgroupsvocabulary'),
        required=False,
        default=[],
    )

    # AT condition: python: here.attribute_is_used('category')
    # AT vocabulary: 'listCategories' (instance method) — wrap in IVocabularyFactory in B.2.x.
    category = schema.Choice(
        title=_(u'PloneMeeting_label_category', default=u'Category'),
        description=_(u'item_category_descr', default=u'Category'),
        vocabulary=u'Products.PloneMeeting.vocabularies.item_categories_vocabulary',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('classifier')
    # AT vocabulary: 'listClassifiers' — wrap in IVocabularyFactory in B.2.x.
    classifier = schema.Choice(
        title=_(u'PloneMeeting_label_classifier', default=u'Classifier'),
        description=_(u'item_classifier_descr', default=u'Classifier'),
        vocabulary=u'Products.PloneMeeting.vocabularies.item_classifiers_vocabulary',
        required=False,
    )

    # AT condition: python: here.show_committees()
    committees = schema.List(
        title=_(u'PloneMeeting_label_committees', default=u'Committees'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.item_selectable_committees_vocabulary'),
        required=True,
        default=[],
    )

    # AT condition: python: here.adapted().mayChangeListType()
    list_type = schema.Choice(
        title=_(u'PloneMeeting_label_listType', default=u'Listtype'),
        vocabulary=u'Products.PloneMeeting.vocabularies.listtypesvocabulary',
        required=False,
        default=u'normal',
    )

    # AT condition: python: here.showEmergency()
    # AT vocabulary: 'listEmergencies' — wrap in IVocabularyFactory in B.2.x.
    emergency = schema.Choice(
        title=_(u'PloneMeeting_label_emergency', default=u'Emergency'),
        description=_(u'item_emergency_descr', default=u'Emergency'),
        vocabulary=u'Products.PloneMeeting.vocabularies.item_emergencies_vocabulary',
        required=False,
        default=u'no_emergency',
    )

    # AT condition: not here.isDefinedInTool()
    # AT vocabulary: 'listMeetingsAcceptingItems' — wrap in IVocabularyFactory in B.2.x.
    preferred_meeting = schema.Choice(
        title=_(u'PloneMeeting_label_preferredMeeting', default=u'Preferredmeeting'),
        description=_(u'preferred_meeting_descr', default=u'Preferredmeeting'),
        vocabulary=u'Products.PloneMeeting.vocabularies.item_meetings_accepting_items_vocabulary',
        required=False,
        default=ITEM_NO_PREFERRED_MEETING_VALUE,
    )

    # AT condition: here.attribute_is_used('meetingDeadlineDate') and not here.isDefinedInTool()
    meeting_deadline_date = schema.Datetime(
        title=_(u'PloneMeeting_label_meetingDeadlineDate', default=u'Meetingdeadlinedate'),
        description=_(u'meeting_deadline_date_descr', default=u'Meetingdeadlinedate'),
        required=False,
    )

    # AT condition: python: here.attribute_is_used('itemTags')
    # AT vocabulary: 'listItemTags' — wrap in IVocabularyFactory in B.2.x.
    item_tags = schema.List(
        title=_(u'PloneMeeting_label_itemTags', default=u'Itemtags'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.item_tags_vocabulary'),
        required=False,
        default=[],
    )

    # AT condition: python: here.attribute_is_used('itemKeywords')
    item_keywords = schema.TextLine(
        title=_(u'PloneMeeting_label_itemKeywords', default=u'Itemkeywords'),
        required=False,
    )

    # AT condition: python: here.showOptionalAdvisers()
    optional_advisers = schema.List(
        title=_(u'PloneMeeting_label_optionalAdvisers', default=u'Optionaladvisers'),
        description=_(u'optional_advisers_item_descr', default=u'OptionalAdvisersItem'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.itemoptionaladvicesvocabulary'),
        required=False,
        default=[],
    )

    # AT condition: python: here.attribute_is_used('emergencyMotivation')
    form.read_permission(emergency_motivation=READ_DECISION)
    form.write_permission(emergency_motivation=WriteDecision)
    emergency_motivation = RichText(
        title=_(u'PloneMeeting_label_emergencyMotivation', default=u'Emergencymotivation'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('motivation')
    form.read_permission(motivation=READ_DECISION)
    form.write_permission(motivation=WriteDecision)
    motivation = RichText(
        title=_(u'PloneMeeting_label_motivation', default=u'Motivation'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT: required field (optional=False).
    form.read_permission(decision=READ_DECISION)
    form.write_permission(decision=WriteDecision)
    decision = RichText(
        title=_(u'PloneMeeting_label_decision', default=u'Decision'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=True,
    )

    # AT condition: python: here.attribute_is_used('decisionSuite')
    form.read_permission(decision_suite=READ_DECISION)
    form.write_permission(decision_suite=WriteDecision)
    decision_suite = RichText(
        title=_(u'PloneMeeting_label_decisionSuite', default=u'Decisionsuite'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('decisionEnd')
    form.read_permission(decision_end=READ_DECISION)
    form.write_permission(decision_end=WriteDecision)
    decision_end = RichText(
        title=_(u'PloneMeeting_label_decisionEnd', default=u'Decisionend'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('votesResult')
    # AT note: write_permission=WriteMarginalNotes (intentional — see AT comment).
    form.read_permission(votes_result=READ_DECISION)
    form.write_permission(votes_result=WriteMarginalNotes)
    votes_result = RichText(
        title=_(u'PloneMeeting_label_votesResult', default=u'Votesresult'),
        description=_(u'votes_result_descr', default=u'Votesresult'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.showOralQuestion()
    oral_question = schema.Bool(
        title=_(u'PloneMeeting_label_oralQuestion', default=u'Oralquestion'),
        description=_(u'oral_question_item_descr', default=u'OralQuestion'),
        required=False,
        default=False,
    )

    # AT condition: python: here.showToDiscuss()
    # AT default_method: getDefaultToDiscuss (B.2.x: wire as defaultFactory).
    to_discuss = schema.Bool(
        title=_(u'PloneMeeting_label_toDiscuss', default=u'Todiscuss'),
        required=False,
    )

    # AT condition: python: here.attribute_is_used('itemInitiator')
    # AT vocabulary: 'listItemInitiators' — wrap in IVocabularyFactory in B.2.x.
    item_initiator = schema.List(
        title=_(u'PloneMeeting_label_itemInitiator', default=u'Iteminitiator'),
        description=_(u'item_initiator_descr', default=u'Iteminitiator'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.item_initiators_vocabulary'),
        required=False,
        default=[],
    )

    # AT condition: python: here.adapted().show_field('groupsInChargeNotes')
    form.write_permission(groups_in_charge_notes='View')
    groups_in_charge_notes = RichText(
        title=_(u'PloneMeeting_label_groupsInChargeNotes', default=u'Groupsinchargenotes'),
        description=_(u'groups_in_charge_notes_descr', default=u'Groupsinchargenotes'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.showMeetingManagerReservedField('inAndOutMoves')
    form.write_permission(in_and_out_moves=WriteItemMeetingManagerFields)
    in_and_out_moves = RichText(
        title=_(u'PloneMeeting_inAndOutMoves', default=u'Inandoutmoves'),
        description=_(u'descr_field_reserved_to_meeting_managers', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.showMeetingManagerReservedField('notes')
    form.write_permission(notes=WriteItemMeetingManagerFields)
    notes = RichText(
        title=_(u'PloneMeeting_notes', default=u'Notes'),
        description=_(u'descr_field_reserved_to_meeting_managers', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.showMeetingManagerReservedField('meetingManagersNotes')
    form.write_permission(meeting_managers_notes=WriteItemMeetingManagerFields)
    meeting_managers_notes = RichText(
        title=_(u'PloneMeeting_label_meetingManagersNotes', default=u'Meetingmanagersnotes'),
        description=_(u'descr_field_reserved_to_meeting_managers', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.showMeetingManagerReservedField('meetingManagersNotesSuite')
    form.write_permission(meeting_managers_notes_suite=WriteItemMeetingManagerFields)
    meeting_managers_notes_suite = RichText(
        title=_(u'PloneMeeting_label_meetingManagersNotesSuite',
                default=u'Meetingmanagersnotessuite'),
        description=_(u'descr_field_reserved_to_meeting_managers', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.showMeetingManagerReservedField('meetingManagersNotesEnd')
    form.write_permission(meeting_managers_notes_end=WriteItemMeetingManagerFields)
    meeting_managers_notes_end = RichText(
        title=_(u'PloneMeeting_label_meetingManagersNotesEnd',
                default=u'Meetingmanagersnotesend'),
        description=_(u'descr_field_reserved_to_meeting_managers', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('internalNotes')
    # AT note: read_permission == write_permission == WriteInternalNotes.
    form.read_permission(internal_notes=WriteInternalNotes)
    form.write_permission(internal_notes=WriteInternalNotes)
    internal_notes = RichText(
        title=_(u'PloneMeeting_label_internalNotes', default=u'Internalnotes'),
        description=_(u'internal_notes_descr', default=u'Internalnotes'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.adapted().show_field('neededFollowUp')
    form.write_permission(needed_follow_up='View')
    needed_follow_up = RichText(
        title=_(u'PloneMeeting_label_neededFollowUp', default=u'Neededfollowup'),
        description=_(u'needed_follow_up_descr', default=u'Neededfollowup'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.adapted().show_field('providedFollowUp')
    form.write_permission(provided_follow_up='View')
    provided_follow_up = RichText(
        title=_(u'PloneMeeting_label_providedFollowUp', default=u'Providedfollowup'),
        description=_(u'provided_follow_up_descr', default=u'Providedfollowup'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('marginalNotes')
    form.write_permission(marginal_notes=WriteMarginalNotes)
    marginal_notes = RichText(
        title=_(u'PloneMeeting_label_marginalNotes', default=u'Marginalnotes'),
        description=_(u'marginal_notes_descr', default=u'Marginalnotes'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.adapted().showObservations()
    form.read_permission(observations=READ_OBSERVATIONS)
    form.write_permission(observations=WriteItemMeetingManagerFields)
    observations = RichText(
        title=_(u'PloneMeeting_itemObservations', default=u'Observations'),
        description=_(u'descr_field_vieawable_by_everyone', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.isDefinedInTool(item_type='itemtemplate')
    template_using_groups = schema.List(
        title=_(u'PloneMeeting_label_templateUsingGroups', default=u'Templateusinggroups'),
        description=_(u'template_using_groups_descr', default=u'Templateusinggroups'),
        value_type=schema.Choice(
            vocabulary=u'collective.contact.plonegroup.browser.settings.'
                       u'SortedSelectedOrganizationsElephantVocabulary'),
        required=False,
        default=[],
    )

    # AT condition: here.isDefinedInTool(item_type='recurring')
    # AT vocabulary: 'listMeetingTransitions' — wrap in IVocabularyFactory in B.2.x.
    meeting_transition_inserting_me = schema.Choice(
        title=_(u'PloneMeeting_label_meetingTransitionInsertingMe',
                default=u'Meetingtransitioninsertingme'),
        description=_(u'meeting_transition_inserting_me_descr',
                      default=u'Meetingtransitioninsertingme'),
        vocabulary=u'Products.PloneMeeting.vocabularies.item_meeting_transitions_vocabulary',
        required=False,
    )

    # AT condition: python: here.is_assembly_field_used('itemAssembly')
    # AT widget: TextAreaWidget (text/plain).
    item_assembly = schema.Text(
        title=_(u'PloneMeeting_label_itemAssembly', default=u'Itemassembly'),
        description=_(u'item_assembly_descr', default=u'Itemassembly'),
        required=False,
    )

    # AT condition: python: here.is_assembly_field_used('itemAssemblyExcused')
    item_assembly_excused = schema.Text(
        title=_(u'PloneMeeting_label_itemAssemblyExcused', default=u'Itemassemblyexcused'),
        description=_(u'item_assembly_excused_descr', default=u'Itemassemblyexcused'),
        required=False,
    )

    # AT condition: python: here.is_assembly_field_used('itemAssemblyAbsents')
    item_assembly_absents = schema.Text(
        title=_(u'PloneMeeting_label_itemAssemblyAbsents', default=u'Itemassemblyabsents'),
        description=_(u'item_assembly_absents_descr', default=u'Itemassemblyabsents'),
        required=False,
    )

    # AT condition: python: here.is_assembly_field_used('itemAssemblyGuests')
    item_assembly_guests = schema.Text(
        title=_(u'PloneMeeting_label_itemAssemblyGuests', default=u'Itemassemblyguests'),
        description=_(u'item_assembly_guests_descr', default=u'Itemassemblyguests'),
        required=False,
    )

    # AT condition: python: here.is_assembly_field_used('itemSignatures')
    item_signatures = schema.Text(
        title=_(u'PloneMeeting_label_itemSignatures', default=u'Itemsignatures'),
        description=_(u'item_signatures_descr', default=u'Itemsignatures'),
        required=False,
    )

    # AT condition: python: here.attribute_is_used('copyGroups')
    copy_groups = schema.List(
        title=_(u'PloneMeeting_label_copyGroups', default=u'Copygroups'),
        description=_(u'copy_groups_item_descr', default=u'Copygroupsitems'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.itemcopygroupsvocabulary'),
        required=False,
        default=[],
    )

    # AT condition: python: here.attribute_is_used('restrictedCopyGroups')
    form.write_permission(restricted_copy_groups=WriteItemMeetingManagerFields)
    restricted_copy_groups = schema.List(
        title=_(u'PloneMeeting_label_restrictedCopyGroups', default=u'Restrictedcopygroups'),
        description=_(u'descr_field_vieawable_by_everyone', default=u''),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.itemrestrictedcopygroupsvocabulary'),
        required=False,
        default=[],
    )

    # AT condition: (here.attribute_is_used('pollType') or here.isVotesEnabled())
    #   and here.adapted().mayChangePollType()
    # AT default_method: getDefaultPollType (B.2.x: wire as defaultFactory).
    poll_type = schema.Choice(
        title=_(u'PloneMeeting_label_pollType', default=u'Polltype'),
        vocabulary=u'Products.PloneMeeting.vocabularies.polltypesvocabulary',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('pollTypeObservations')
    form.write_permission(poll_type_observations=WriteItemMeetingManagerFields)
    poll_type_observations = RichText(
        title=_(u'PloneMeeting_label_pollTypeObservations', default=u'Polltypeobservations'),
        description=_(u'descr_field_vieawable_by_everyone', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('committeeObservations')
    form.write_permission(committee_observations=WriteCommitteeFields)
    committee_observations = RichText(
        title=_(u'PloneMeeting_label_committeeObservations', default=u'Committeeobservations'),
        description=_(u'descr_field_editable_by_committee_editors', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.attribute_is_used('committeeTranscript')
    form.write_permission(committee_transcript=WriteCommitteeFields)
    committee_transcript = RichText(
        title=_(u'PloneMeeting_label_committeeTranscript', default=u'Committeetranscript'),
        description=_(u'descr_field_vieawable_by_committee_editors', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.adapted().show_votesObservations()
    form.write_permission(votes_observations=WriteItemMeetingManagerFields)
    votes_observations = RichText(
        title=_(u'PloneMeeting_label_votesObservations', default=u'Votesobservations'),
        description=_(u'field_vieawable_by_everyone_once_item_decided_descr', default=u''),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.attribute_is_used('manuallyLinkedItems') and not here.isDefinedInTool()
    # AT type: ReferenceField(relationship='ManuallyLinkedItem', multiValued=True).
    # B.2.x will switch to z3c.relationfield.RelationList; for now we store UID strings.
    manually_linked_items = schema.List(
        title=_(u'PloneMeeting_label_manuallyLinkedItems', default=u'Manuallylinkeditems'),
        description=_(u'manually_linked_items_descr', default=u'Manuallylinkeditems'),
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    # AT condition: python: here.showClonableToOtherMCs()
    other_meeting_configs_clonable_to = schema.List(
        title=_(u'PloneMeeting_label_otherMeetingConfigsClonableTo',
                default=u'Othermeetingconfigsclonableto'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.other_mcs_clonable_to_vocabulary'),
        required=False,
        default=[],
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToEmergency')
    other_meeting_configs_clonable_to_emergency = schema.List(
        title=_(u'PloneMeeting_label_otherMeetingConfigsClonableToEmergency',
                default=u'Othermeetingconfigsclonabletoemergency'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.'
                       u'other_mcs_clonable_to_emergency_vocabulary'),
        required=False,
        default=[],
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToPrivacy')
    other_meeting_configs_clonable_to_privacy = schema.List(
        title=_(u'PloneMeeting_label_otherMeetingConfigsClonableToPrivacy',
                default=u'Othermeetingconfigsclonabletoprivacy'),
        value_type=schema.Choice(
            vocabulary=u'Products.PloneMeeting.vocabularies.'
                       u'other_mcs_clonable_to_privacy_vocabulary'),
        required=False,
        default=[],
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldTitle')
    other_meeting_configs_clonable_to_field_title = schema.TextLine(
        title=_(u'PloneMeeting_label_itemTitle', default=u'OtherMeetingConfigsClonableToFieldTitle'),
        required=False,
        default=u'',
        max_length=750,
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldDescription')
    other_meeting_configs_clonable_to_field_description = RichText(
        title=_(u'PloneMeeting_label_itemDescription', default=u'Description'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldDetailedDescription')
    other_meeting_configs_clonable_to_field_detailed_description = RichText(
        title=_(u'PloneMeeting_label_detailedDescription', default=u'Detaileddescription'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldMotivation')
    form.read_permission(other_meeting_configs_clonable_to_field_motivation=READ_DECISION)
    form.write_permission(other_meeting_configs_clonable_to_field_motivation=WriteDecision)
    other_meeting_configs_clonable_to_field_motivation = RichText(
        title=_(u'PloneMeeting_label_motivation', default=u'Othermeetingconfigsclonabletofieldmotivation'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldDecision')
    form.read_permission(other_meeting_configs_clonable_to_field_decision=READ_DECISION)
    form.write_permission(other_meeting_configs_clonable_to_field_decision=WriteDecision)
    other_meeting_configs_clonable_to_field_decision = RichText(
        title=_(u'PloneMeeting_label_decision', default=u'Othermeetingconfigsclonabletofielddecision'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldDecisionSuite')
    form.read_permission(other_meeting_configs_clonable_to_field_decision_suite=READ_DECISION)
    form.write_permission(other_meeting_configs_clonable_to_field_decision_suite=WriteDecision)
    other_meeting_configs_clonable_to_field_decision_suite = RichText(
        title=_(u'PloneMeeting_label_decisionSuite',
                default=u'Othermeetingconfigsclonabletofielddecisionsuite'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: here.attribute_is_used('otherMeetingConfigsClonableToFieldDecisionEnd')
    form.read_permission(other_meeting_configs_clonable_to_field_decision_end=READ_DECISION)
    form.write_permission(other_meeting_configs_clonable_to_field_decision_end=WriteDecision)
    other_meeting_configs_clonable_to_field_decision_end = RichText(
        title=_(u'PloneMeeting_label_decisionEnd',
                default=u'Othermeetingconfigsclonabletofielddecisionend'),
        default_mime_type='text/html',
        allowed_mime_types=('text/html',),
        output_mime_type='text/x-html-safe',
        required=False,
    )

    # AT condition: python: here.showIsAcceptableOutOfMeeting()
    is_acceptable_out_of_meeting = schema.Bool(
        title=_(u'PloneMeeting_label_isAcceptableOutOfMeeting',
                default=u'Isacceptableoutofmeeting'),
        description=_(u'is_acceptable_out_of_meeting_descr',
                      default=u'Isacceptableoutofmeeting'),
        required=False,
        default=False,
    )

    # AT condition: python: here.attribute_is_used('sendToAuthority')
    send_to_authority = schema.Bool(
        title=_(u'PloneMeeting_label_sendToAuthority', default=u'Sendtoauthority'),
        description=_(u'send_to_authority_descr', default=u'Sendtoauthority'),
        required=False,
        default=False,
    )

    # AT condition: python: here.attribute_is_used('privacy')
    privacy = schema.Choice(
        title=_(u'PloneMeeting_label_privacy', default=u'Privacy'),
        vocabulary=u'Products.PloneMeeting.vocabularies.privaciesvocabulary',
        required=False,
        default=u'public',
    )

    # AT condition: here.attribute_is_used('completeness') and
    #   (here.adapted().mayEvaluateCompleteness() or here.adapted().mayAskCompletenessEvalAgain())
    # AT vocabulary: 'listCompleteness' — wrap in IVocabularyFactory in B.2.x.
    completeness = schema.Choice(
        title=_(u'PloneMeeting_label_completeness', default=u'Completeness'),
        description=_(u'item_completeness_descr', default=u'Completeness'),
        vocabulary=u'Products.PloneMeeting.vocabularies.item_completeness_vocabulary',
        required=False,
        default=u'completeness_not_yet_evaluated',
    )

    # AT condition: python: here.showItemIsSigned()
    item_is_signed = schema.Bool(
        title=_(u'PloneMeeting_label_itemIsSigned', default=u'Itemissigned'),
        required=False,
        default=False,
    )

    # AT condition: python: here.attribute_is_used('takenOverBy')
    taken_over_by = schema.TextLine(
        title=_(u'PloneMeeting_label_takenOverBy', default=u'Takenoverby'),
        required=False,
    )

    # AT condition: here.showMeetingManagerReservedField('textCheckList')
    # AT widget: TextAreaWidget (text/plain).
    form.write_permission(text_check_list=WriteItemMeetingManagerFields)
    text_check_list = schema.Text(
        title=_(u'PloneMeeting_label_textCheckList', default=u'Textchecklist'),
        description=_(u'text_check_list_descr',
                      default=u'Enter elements that are necessary for this kind of item'),
        required=False,
    )


# ---------------------------------------------------------------------------
# Schema policy
# ---------------------------------------------------------------------------

class MeetingItemSchemaPolicy(DexteritySchemaPolicy):
    """Schema policy for MeetingItem."""

    def bases(self, schema_policy, schema):
        return (IMeetingItem, )


# ---------------------------------------------------------------------------
# Content class skeleton
# ---------------------------------------------------------------------------

class MeetingItem(Container):
    """Meeting item content type (migrated from Archetypes OrderedBaseFolder).

    B.2.0 ships only the schema and a placeholder class; the FTI swap and
    AT compatibility shims (``getField``, ``processForm``, ``validate``,
    ``Title`` override, business methods) land in B.2.1+. Until then,
    the active runtime class is still ``Products.PloneMeeting.MeetingItem``
    (Archetypes).
    """

    implements(IMeetingItem)
    security = ClassSecurityInfo()

    meta_type = 'MeetingItem'
