# -*- coding: utf-8 -*-
"""AT (camelCase) -> DX (snake_case) field-name mappings for the
Plone 4.3 -> 6.1 collective.exportimport migration.

Sources of truth: MIGRATION_SUMMARY_MEETINGITEM.md and
MIGRATION_SUMMARY_MEETINGCONFIG.md, cross-checked against
content/meetingitem.py and content/meetingconfig.py, and against the
legacy AT schemas kept in MeetingItem.py / MeetingConfig.py.

The AT export (plone.restapi 7.9.1 serializers) emits field names
exactly as declared on the AT schema; every rename happens here, at
import time. Identity pairs are omitted: only names that actually
differ are listed.
"""

# MeetingItem and its subtypes (MeetingItemTemplate, MeetingItemRecurring,
# plus every per-config cloned FTI, e.g. MeetingItemCollege).
MEETINGITEM_AT_TO_DX = {
    "itemNumber": "item_number",
    "itemReference": "item_reference",
    "detailedDescription": "detailed_description",
    "budgetRelated": "budget_related",
    "budgetInfos": "budget_infos",
    "proposingGroup": "proposing_group",
    "proposingGroupWithGroupInCharge": "proposing_group_with_group_in_charge",
    "groupsInCharge": "groups_in_charge",
    "associatedGroups": "associated_groups",
    "listType": "list_type",
    "preferredMeeting": "preferred_meeting",
    "meetingDeadlineDate": "meeting_deadline_date",
    "itemTags": "item_tags",
    "itemKeywords": "item_keywords",
    "optionalAdvisers": "optional_advisers",
    "emergencyMotivation": "emergency_motivation",
    "decisionSuite": "decision_suite",
    "decisionEnd": "decision_end",
    "votesResult": "votes_result",
    "oralQuestion": "oral_question",
    "toDiscuss": "to_discuss",
    "itemInitiator": "item_initiator",
    "groupsInChargeNotes": "groups_in_charge_notes",
    "inAndOutMoves": "in_and_out_moves",
    "meetingManagersNotes": "meeting_managers_notes",
    "meetingManagersNotesSuite": "meeting_managers_notes_suite",
    "meetingManagersNotesEnd": "meeting_managers_notes_end",
    "internalNotes": "internal_notes",
    "neededFollowUp": "needed_follow_up",
    "providedFollowUp": "provided_follow_up",
    "marginalNotes": "marginal_notes",
    "templateUsingGroups": "template_using_groups",
    "meetingTransitionInsertingMe": "meeting_transition_inserting_me",
    "itemAssembly": "item_assembly",
    "itemAssemblyExcused": "item_assembly_excused",
    "itemAssemblyAbsents": "item_assembly_absents",
    "itemAssemblyGuests": "item_assembly_guests",
    "itemSignatures": "item_signatures",
    "copyGroups": "copy_groups",
    "restrictedCopyGroups": "restricted_copy_groups",
    "pollType": "poll_type",
    "pollTypeObservations": "poll_type_observations",
    "committeeObservations": "committee_observations",
    "committeeTranscript": "committee_transcript",
    "votesObservations": "votes_observations",
    "manuallyLinkedItems": "manually_linked_items",
    "otherMeetingConfigsClonableTo": "other_meeting_configs_clonable_to",
    "otherMeetingConfigsClonableToEmergency":
        "other_meeting_configs_clonable_to_emergency",
    "otherMeetingConfigsClonableToPrivacy":
        "other_meeting_configs_clonable_to_privacy",
    "otherMeetingConfigsClonableToFieldTitle":
        "other_meeting_configs_clonable_to_field_title",
    "otherMeetingConfigsClonableToFieldDescription":
        "other_meeting_configs_clonable_to_field_description",
    "otherMeetingConfigsClonableToFieldDetailedDescription":
        "other_meeting_configs_clonable_to_field_detailed_description",
    "otherMeetingConfigsClonableToFieldMotivation":
        "other_meeting_configs_clonable_to_field_motivation",
    "otherMeetingConfigsClonableToFieldDecision":
        "other_meeting_configs_clonable_to_field_decision",
    "otherMeetingConfigsClonableToFieldDecisionSuite":
        "other_meeting_configs_clonable_to_field_decision_suite",
    "otherMeetingConfigsClonableToFieldDecisionEnd":
        "other_meeting_configs_clonable_to_field_decision_end",
    "isAcceptableOutOfMeeting": "is_acceptable_out_of_meeting",
    "sendToAuthority": "send_to_authority",
    "itemIsSigned": "item_is_signed",
    "takenOverBy": "taken_over_by",
    "textCheckList": "text_check_list",
}

MEETINGCONFIG_AT_TO_DX = {
    "adviceAnnexConfidentialVisibleFor": "advice_annex_confidential_visible_for",
    "adviceConfidentialFor": "advice_confidential_for",
    "adviceConfidentialityDefault": "advice_confidentiality_default",
    "adviceStyle": "advice_style",
    "advicesKeptOnSentToOtherMC": "advices_kept_on_sent_to_other_mc",
    "allItemTags": "all_item_tags",
    "annexEditorMayInsertBarcode": "annex_editor_may_insert_barcode",
    "annexRestrictShownAndEditableAttributes":
        "annex_restrict_shown_and_editable_attributes",
    "annexToPrintMode": "annex_to_print_mode",
    "assemblyStaves": "assembly_staves",
    "availableItemsListVisibleColumns": "available_items_list_visible_columns",
    "certifiedSignatures": "certified_signatures",
    "computeItemReferenceForItemsOutOfMeeting":
        "compute_item_reference_for_items_out_of_meeting",
    "configGroup": "config_group",
    "configVersion": "config_version",
    "contentsKeptOnSentToOtherMC": "contents_kept_on_sent_to_other_mc",
    "cssTransforms": "css_transforms",
    "customAdvisers": "custom_advisers",
    "dashboardItemsListingsFilters": "dashboard_items_listings_filters",
    "dashboardMeetingAvailableItemsFilters":
        "dashboard_meeting_available_items_filters",
    "dashboardMeetingLinkedItemsFilters":
        "dashboard_meeting_linked_items_filters",
    "dashboardMeetingsListingsFilters": "dashboard_meetings_listings_filters",
    "defaultAdviceHiddenDuringRedaction":
        "default_advice_hidden_during_redaction",
    "defaultAdviceType": "default_advice_type",
    "defaultPollType": "default_poll_type",
    "displayAvailableItemsTo": "display_available_items_to",
    "displayVotingGroup": "display_voting_group",
    "enableAddQuickAdvice": "enable_add_quick_advice",
    "enableAdviceConfidentiality": "enable_advice_confidentiality",
    "enableAdviceInvalidation": "enable_advice_invalidation",
    "enableAdviceProposingGroupComment": "enable_advice_proposing_group_comment",
    "enabledAnnexesBatchActions": "enabled_annexes_batch_actions",
    "enabledItemActions": "enabled_item_actions",
    "enforceAdviceMandatoriness": "enforce_advice_mandatoriness",
    "firstLinkedVoteUsedVoteValues": "first_linked_vote_used_vote_values",
    "folderTitle": "folder_title",
    "freezeDeadlineDefault": "freeze_deadline_default",
    "groupsHiddenInDashboardFilter": "groups_hidden_in_dashboard_filter",
    "historizeAdviceIfGivenAndItemModified":
        "historize_advice_if_given_and_item_modified",
    "historizeItemDataWhenAdviceIsGiven":
        "historize_item_data_when_advice_is_given",
    "historizedItemAttributes": "historized_item_attributes",
    "includeGroupsInChargeDefinedOnCategory":
        "include_groups_in_charge_defined_on_category",
    "includeGroupsInChargeDefinedOnProposingGroup":
        "include_groups_in_charge_defined_on_proposing_group",
    "inheritedAdviceRemoveableByAdviser":
        "inherited_advice_removeable_by_adviser",
    "insertingMethodsOnAddItem": "inserting_methods_on_add_item",
    "isDefault": "is_default",
    "itemActionsColumnConfig": "item_actions_column_config",
    "itemActionsInterface": "item_actions_interface",
    "itemAdviceEditStates": "item_advice_edit_states",
    "itemAdviceInvalidateStates": "item_advice_invalidate_states",
    "itemAdviceStates": "item_advice_states",
    "itemAdviceViewStates": "item_advice_view_states",
    "itemAnnexConfidentialVisibleFor": "item_annex_confidential_visible_for",
    "itemAutoSentToOtherMCStates": "item_auto_sent_to_other_mc_states",
    "itemBudgetInfosStates": "item_budget_infos_states",
    "itemColumns": "item_columns",
    "itemCommitteesStates": "item_committees_states",
    "itemCommitteesViewStates": "item_committees_view_states",
    "itemConditionsInterface": "item_conditions_interface",
    "itemCopyGroupsStates": "item_copy_groups_states",
    "itemFieldsToKeepConfigSortingFor": "item_fields_to_keep_config_sorting_for",
    "itemGroupsInChargeStates": "item_groups_in_charge_states",
    "itemIconColor": "item_icon_color",
    "itemManualSentToOtherMCStates": "item_manual_sent_to_other_mc_states",
    "itemObserversStates": "item_observers_states",
    "itemPreferredMeetingStates": "item_preferred_meeting_states",
    "itemReferenceFormat": "item_reference_format",
    "itemWFValidationLevels": "item_wf_validation_levels",
    "itemWithGivenAdviceIsNotDeletable": "item_with_given_advice_is_not_deletable",
    "itemWorkflow": "item_workflow",
    "itemsListVisibleColumns": "items_list_visible_columns",
    "itemsListVisibleFields": "items_list_visible_fields",
    "itemsNotViewableVisibleFields": "items_not_viewable_visible_fields",
    "itemsNotViewableVisibleFieldsTALExpr":
        "items_not_viewable_visible_fields_tal_expr",
    "itemsVisibleFields": "items_visible_fields",
    "keepAccessToItemWhenAdvice": "keep_access_to_item_when_advice",
    "keepOriginalToPrintOfClonedItems": "keep_original_to_print_of_cloned_items",
    "lastMeetingNumber": "last_meeting_number",
    "listTypes": "list_types",
    "mailItemEvents": "mail_item_events",
    "mailMeetingEvents": "mail_meeting_events",
    "mailMode": "mail_mode",
    "maxShownAvailableItems": "max_shown_available_items",
    "maxShownListings": "max_shown_listings",
    "maxShownMeetingItems": "max_shown_meeting_items",
    "maxShownMeetings": "max_shown_meetings",
    "meetingActionsInterface": "meeting_actions_interface",
    "meetingAnnexConfidentialVisibleFor":
        "meeting_annex_confidential_visible_for",
    "meetingColumns": "meeting_columns",
    "meetingConditionsInterface": "meeting_conditions_interface",
    "meetingConfigsToCloneTo": "meeting_configs_to_clone_to",
    "meetingItemTemplatesToStoreAsAnnex":
        "meeting_item_templates_to_store_as_annex",
    "meetingPresentItemWhenNoCurrentMeetingStates":
        "meeting_present_item_when_no_current_meeting_states",
    "meetingWorkflow": "meeting_workflow",
    "onMeetingTransitionItemActionToExecute":
        "on_meeting_transition_item_action_to_execute",
    "onTransitionFieldTransforms": "on_transition_field_transforms",
    "orderedAssociatedOrganizations": "ordered_associated_organizations",
    "orderedCommitteeContacts": "ordered_committee_contacts",
    "orderedContacts": "ordered_contacts",
    "orderedGroupsInCharge": "ordered_groups_in_charge",
    "orderedItemInitiators": "ordered_item_initiators",
    "powerAdvisersGroups": "power_advisers_groups",
    "powerObservers": "power_observers",
    "recordItemHistoryStates": "record_item_history_states",
    "redirectToNextMeeting": "redirect_to_next_meeting",
    "removeAnnexesPreviewsOnMeetingClosure":
        "remove_annexes_previews_on_meeting_closure",
    "selectableAdviserUsers": "selectable_adviser_users",
    "selectableAdvisers": "selectable_advisers",
    "selectablePrivacies": "selectable_privacies",
    "selectableRedefinedPositionTypes": "selectable_redefined_position_types",
    "shortName": "short_name",
    "sortAllItemTags": "sort_all_item_tags",
    "toDiscussDefault": "to_discuss_default",
    "toDiscussLateDefault": "to_discuss_late_default",
    "toDiscussSetOnItemInsert": "to_discuss_set_on_item_insert",
    "toDoListSearches": "to_do_list_searches",
    "transitionsReinitializingDelays": "transitions_reinitializing_delays",
    "transitionsToConfirm": "transitions_to_confirm",
    "useAdvices": "use_advices",
    "usedAdviceTypes": "used_advice_types",
    "usedItemAttributes": "used_item_attributes",
    "usedMeetingAttributes": "used_meeting_attributes",
    "usersHiddenInDashboardFilter": "users_hidden_in_dashboard_filter",
    "usingGroups": "using_groups",
    "validationDeadlineDefault": "validation_deadline_default",
    "wfAdaptations": "wf_adaptations",
    "xhtmlTransformFields": "xhtml_transform_fields",
    "xhtmlTransformTypes": "xhtml_transform_types",
    "yearlyInitMeetingNumbers": "yearly_init_meeting_numbers",
    # The 20 fields absent from the MIGRATION_SUMMARY_MEETINGCONFIG.md rename
    # table (doc lists 133/153); AT names verified against MeetingConfig.py.
    # NB: the doc wrongly claims budgetDefault was removed — budget_default
    # exists in IMeetingConfig and must be migrated.
    "budgetDefault": "budget_default",
    "selectableCopyGroups": "selectable_copy_groups",
    "selectableRestrictedCopyGroups": "selectable_restricted_copy_groups",
    "itemRestrictedCopyGroupsStates": "item_restricted_copy_groups_states",
    "hideHistoryTo": "hide_history_to",
    "hideItemHistoryCommentsToUsersOutsideProposingGroup":
        "hide_item_history_comments_to_users_outside_proposing_group",
    "hideNotViewableLinkedItemsTo": "hide_not_viewable_linked_items_to",
    "restrictAccessToSecretItems": "restrict_access_to_secret_items",
    "restrictAccessToSecretItemsTo": "restrict_access_to_secret_items_to",
    "ownerMayDeleteAnnexDecision": "owner_may_delete_annex_decision",
    "labelsConfig": "labels_config",
    "itemInternalNotesEditableBy": "item_internal_notes_editable_by",
    "itemFieldsConfig": "item_fields_config",
    "useVotes": "use_votes",
    "votesEncoder": "votes_encoder",
    "usedPollTypes": "used_poll_types",
    "usedVoteValues": "used_vote_values",
    "nextLinkedVotesUsedVoteValues": "next_linked_votes_used_vote_values",
    "voteCondition": "vote_condition",
    "votesResultTALExpr": "votes_result_tal_expr",
}

# AT TextFields that became plain schema.Text (not RichText): the AT
# serializer exports them as {"content-type": "text/plain", "data": ...}
# dicts, but the DX schema.Text deserializer expects a plain string.
# Keys are DX names (applied after renaming).
MEETINGITEM_PLAIN_TEXT_FIELDS = {
    "item_assembly",
    "item_assembly_excused",
    "item_assembly_absents",
    "item_assembly_guests",
    "item_signatures",
    "text_check_list",
}

MEETINGCONFIG_PLAIN_TEXT_FIELDS = {
    "assembly",
    "assembly_staves",
    "signatures",
    "places",
    "all_item_tags",
    "item_reference_format",
    "items_not_viewable_visible_fields_tal_expr",
    "vote_condition",
    "votes_result_tal_expr",
}

# DataGrid row-dict keys that differ between the AT columns and the DX
# DictRow schemas (second, nested camelCase->snake_case layer that the
# top-level maps do not cover). Keys are DX field names; values map
# AT row key -> DX row key. All 13 MeetingConfig grids were compared
# against their I*RowSchema: only these two have renamed columns, the
# other 11 are byte-identical (labels_config only changed column ORDER,
# which is irrelevant when migrating dicts by key).
ROW_KEY_MAPS = {
    "certified_signatures": {"signatureNumber": "signature_number"},
    "inserting_methods_on_add_item": {"insertingMethod": "inserting_method"},
}

# manually_linked_items: AT ReferenceField (relationship
# 'ManuallyLinkedItem') -> DX schema.List of UID strings. The AT export
# serializes reference fields as summaries without a stable UID key, so the
# field is dropped at import and rebuilt from the @@export_relations JSON
# (see @@import_pm_manually_linked_items).
MEETINGITEM_DROP_AT_IMPORT = ["manually_linked_items"]
