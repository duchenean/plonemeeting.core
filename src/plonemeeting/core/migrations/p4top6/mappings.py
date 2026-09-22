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
    # the AT field is "workflowAdaptations"; "wfAdaptations" is a class
    # attribute of the 4.2 MeetingConfig that lists every *available*
    # adaptation, not the selected ones
    "workflowAdaptations": "wf_adaptations",
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

# The contacts directory of the Plone 6 profile already exists when the
# contacts are imported, so collective.exportimport skips it and the
# position types of the 4.3 site are lost. Every held_position then
# fails the position_type constraint. These fields are applied on the
# existing directory instead (see PMImportContent._import_directory).
DIRECTORY_FIELDS = ("position_types",
                    "organization_types",
                    "organization_levels")

# Fields that point at content which does not exist yet when their own
# object is imported. collective.exportimport writes one object at a
# time, the plone.restapi deserializer refuses the whole object when one
# field does not validate, and the references are circular: an
# organization carries the advice settings of a MeetingConfig while a
# MeetingConfig carries organization UIDs. No import order satisfies
# both. These fields travel in a deferred store instead and are applied
# again when their targets exist (see @@import_pm_deferred_fields).
DEFERRED_FIELDS = {
    # organization -> other organizations (groups_in_charge), a
    # held_position (certified_signatures) and MeetingConfig item
    # states (item_advice_*)
    "organization": ("groups_in_charge",
                     "certified_signatures",
                     "item_advice_states",
                     "item_advice_edit_states",
                     "item_advice_view_states"),
    # person -> organization
    "person": ("primary_organization", ),
    # held_position -> organization. The export is sorted by path, so a
    # person that sorts before "plonegroup-organization" holds positions
    # in organizations that are not imported yet.
    "held_position": ("position",
                      "voting_group",
                      "represented_organizations"),
    # a POD template -> other POD templates of the same config (the
    # style, the templates it merges, the mailing loop, the template it
    # reuses) and an annex type of the config, all of them written after
    # it or in another config
    "ConfigurablePODTemplate": ("style_template",
                                "merge_templates",
                                "mailing_loop_template",
                                "pod_template_to_use",
                                "store_as_annex"),
    # a dashboard template -> the DashboardCollections it is shown on,
    # which live in the searches folder of a MeetingConfig, plus the POD
    # template references above
    "DashboardPODTemplate": ("dashboard_collections",
                             "style_template",
                             "merge_templates",
                             "mailing_loop_template",
                             "pod_template_to_use"),
    # an annex type -> another annex type, of this config or of the one
    # the items are sent to
    "ItemAnnexContentCategory": ("after_scan_change_annex_type_to",
                                 "other_mc_correspondences"),
    # a category -> the organizations of the plonegroup registry and the
    # categories of the configs the items are sent to
    "meetingcategory": ("category_mapping_when_cloning_to_other_mc",
                        "groups_in_charge",
                        "using_groups"),
    # a config -> the DashboardCollections of its own searches folder.
    # onConfigInitialized() creates those collections, so the import
    # skips them as existing content and they keep the UID of the new
    # site: the value also goes through the UID map.
    # a config -> objects that are imported after it, or that it stores
    # in another field of its own:
    #   ordered_contacts: held_position UIDs;
    #   advices_kept_on_sent_to_other_mc: rows of its own custom_advisers,
    #     which the deserializer has not stored yet;
    #   meeting_item_templates_to_store_as_annex: its POD templates,
    #     which come after it in the same file.
    # an item -> the meeting it is meant for, which can come later in
    # the same file. The key is the prefix: the item types are cloned
    # per config (MeetingItemCollege, MeetingItemTemplatebp, ...).
    "MeetingItem": ("preferred_meeting", ),
    "MeetingConfig": ("to_do_list_searches",
                      "ordered_contacts",
                      "advices_kept_on_sent_to_other_mc",
                      "meeting_item_templates_to_store_as_annex"),
}

# Dublin Core text fields of every Archetypes type. The 4.3 export
# serializes an AT TextField as {"content-type": ..., "data": ...}; the
# Dexterity types of Plone 6 want a plain string. Without this every
# Folder, Image, File and Document of the 4.3 site fails on
# "description: Object is of wrong type".
DUBLIN_CORE_PLAIN_TEXT_FIELDS = {"description", "rights"}


# The MeetingConfig fields that must be set when the object is created.
# collective.exportimport creates an empty object and deserializes it
# afterwards, but PloneMeeting builds the portal types and the workflows
# of a config on ObjectAddedEvent (tool.invokeFactory("MeetingConfig",
# **data) is the supported path) and the vocabulary of several config
# fields is read from the item workflow. Without these the config gets
# the *base* portal type names, no workflow, and the deserializer raises
# IndexError in getItemWorkflow(). The remaining fields are applied by
# the deserializer and the ObjectModifiedEvent of finish().
CONFIG_FACTORY_FIELDS = ("short_name",
                         "title",
                         "folder_title",
                         "config_group",
                         "item_icon_color",
                         "item_workflow",
                         "meeting_workflow",
                         "item_wf_validation_levels")

# The workflow adaptations cannot travel with CONFIG_FACTORY_FIELDS:
# _performWorkflowAdaptations() reads the "searches" folders of the
# config, and onConfigInitialized() creates them *after* it calls
# registerPortalTypes(). PMImportContent applies them on the created
# object instead, before deserializing, because the item states an
# imported config points at only exist once they are applied.
CONFIG_WF_ADAPTATIONS_FIELD = "wf_adaptations"


# MeetingConfig fields whose *value* is a list of MeetingItem field
# names. They travel in AT camelCase and the Plone 6 vocabulary lists
# the Dexterity names, so the values go through MEETINGITEM_AT_TO_DX
# like the field names themselves.
MEETINGCONFIG_ITEM_FIELD_NAME_FIELDS = (
    "used_item_attributes",
    "historized_item_attributes",
    "item_columns",
    "items_list_visible_columns",
    "available_items_list_visible_columns",
)

# ... the same, with a "MeetingItem." prefix on every value.
MEETINGCONFIG_PREFIXED_ITEM_FIELD_FIELDS = (
    "items_list_visible_fields",
    "items_visible_fields",
    "xhtml_transform_fields",
)

# ... and the DataGrid column that holds one.
MEETINGCONFIG_ITEM_FIELD_NAME_COLUMNS = {"item_fields_config": ("name", )}

# Values of the fields above that are not field names: they place a
# field somewhere else in the item view.
MEETINGITEM_EXTRA_ATTRIBUTE_NAMES = {
    "votesResult_after_motivation": "votes_result_after_motivation",
    "votesResult_after_decision_end": "votes_result_after_decision_end",
}

# DataGrid fields of a MeetingConfig that are set with setattr instead
# of going through the plone.restapi deserializer.
#
# Their rows hold Choice columns whose vocabulary reads the
# MeetingConfig (its item states, its labels, its item fields, the other
# configs), and DictRow validates a row with the row itself as context:
# the vocabulary comes back empty and every value of the column is
# refused. A row is stored as a plain dict of plain values, which is
# exactly what the export carries, and PloneMeeting builds a config the
# same way (tool.invokeFactory("MeetingConfig", **data)).
#
# Only the grids that need it are listed: a grid with a Date or a file
# column does need the deserializer. Add a grid here if a pilot site
# reports it as "Constraint not satisfied" or "Wrong contained type".
MEETINGCONFIG_RAW_GRIDS = ("power_observers",
                           "labels_config",
                           "item_fields_config",
                           "meeting_configs_to_clone_to",
                           "certified_signatures",
                           "committees")

# MeetingConfig fields, grids apart, that are also set with setattr.
#   used_poll_types: its vocabulary is built from its own stored value,
#     so an imported value can never be in it;
#   historized_item_attributes: the Plone 6 vocabulary of item
#     attributes does not offer "title" any more.
MEETINGCONFIG_RAW_FIELDS = ("used_poll_types",
                            "historized_item_attributes")

# A value the new site does not offer, and the value to use instead.
# A 4.3 MeetingConfig can drop a privacy while items keep it; a heading
# privacy is a sub-kind of the base one, so the base one is kept and the
# item stays as closed as it was.
CHOICE_FALLBACKS = {
    "privacy": {"public_heading": "public",
                "secret_heading": "secret"},
}


# Choice fields whose exported value can be a term the new site does
# not offer. Every Archetypes object of the 4.3 site carries a
# "language", and a site that was never multilingual holds "fr-be",
# "en" and the neutral empty token beside its own language. The key is
# dropped and the site language applies.
DROP_UNKNOWN_CHOICE_FIELDS = ("language", )


# A MeetingConfig stores the dotted name of the interfaces that carry
# its workflow conditions and actions
# (Products.MeetingCommunes.interfaces.IMeetingItemCommunesWorkflowConditions
# and the three others). Only the package moved; the class names are
# the same. Add a line for every profile package a pilot site uses.
PACKAGE_RENAMES = {
    "Products.PloneMeeting.": "plonemeeting.core.",
    "Products.MeetingCommunes.": "plonemeeting.communes.",
}
