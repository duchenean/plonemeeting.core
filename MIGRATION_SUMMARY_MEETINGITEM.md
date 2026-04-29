# MeetingItem AT → DX Migration Summary

This document tracks the migration of `MeetingItem` from Archetypes to
Dexterity. It is the punch list for B.2.0 → B.2.8 (see `TODO.md` at the
buildout root for phase planning). The companion document for the
already-landed `MeetingConfig` migration is `MIGRATION_SUMMARY_MEETINGCONFIG.md`.

## Status

| Phase | Scope | State |
|---|---|---|
| B.2.0 | DX schema declaration (`content/meetingitem.py`), schema policy, ZCML utility wiring | **landed** |
| B.2.1 | Infrastructure prep: 6 new vocabulary factories, DX `IObjectAddedEvent` subscriber. **No AT compat shims** — explicit project preference; refactor callers instead. **No FTI swap** — held to end of B.2 so CI stays green. | **landed** |
| B.2.2 | Caller sweep across core modules (`events.py`, `utils.py`, `adapters.py`, `indexes.py`, `Meeting.py`, `ToolPloneMeeting.py`) | pending |
| B.2.3 | Caller sweep across browser layer (`browser/views.py`, `browser/overrides.py`, etc.) | pending |
| B.2.4 | Test suite (`tests/testMeetingItem.py`, `testWFAdaptations.py`, `testViews.py`) | pending |
| B.2.5 | Templates (`browser/templates/*.pt`, `skins/plonemeeting_templates/*.pt` — `meetingitem_view.pt`, `meetingitem_edit.pt`) | pending |
| B.2.6 | Replace `Products.DataGridField` with `collective.z3cform.datagridfield` for grid-style fields | pending |
| B.2.7 | Subtypes (`MeetingItemTemplate`, `MeetingItemRecurring`) re-derive cleanly | pending |
| B.2.8 | FTI swap to Dexterity (last sub-phase). Final cleanup, scrub redundant `MeetingItem.py` self-references, document `getCustomFields(2)` decision. | pending |

## Field renames (camelCase → snake_case)

All 72 AT fields are renamed to snake_case. The transformation is purely
mechanical; there are no irregular renames.

| AT field | DX field |
|---|---|
| `itemNumber` | `item_number` |
| `itemReference` | `item_reference` |
| `description` | `description` |
| `detailedDescription` | `detailed_description` |
| `budgetRelated` | `budget_related` |
| `budgetInfos` | `budget_infos` |
| `proposingGroup` | `proposing_group` |
| `proposingGroupWithGroupInCharge` | `proposing_group_with_group_in_charge` |
| `groupsInCharge` | `groups_in_charge` |
| `associatedGroups` | `associated_groups` |
| `category` | `category` |
| `classifier` | `classifier` |
| `committees` | `committees` |
| `listType` | `list_type` |
| `emergency` | `emergency` |
| `preferredMeeting` | `preferred_meeting` |
| `meetingDeadlineDate` | `meeting_deadline_date` |
| `itemTags` | `item_tags` |
| `itemKeywords` | `item_keywords` |
| `optionalAdvisers` | `optional_advisers` |
| `emergencyMotivation` | `emergency_motivation` |
| `motivation` | `motivation` |
| `decision` | `decision` |
| `decisionSuite` | `decision_suite` |
| `decisionEnd` | `decision_end` |
| `votesResult` | `votes_result` |
| `oralQuestion` | `oral_question` |
| `toDiscuss` | `to_discuss` |
| `itemInitiator` | `item_initiator` |
| `groupsInChargeNotes` | `groups_in_charge_notes` |
| `inAndOutMoves` | `in_and_out_moves` |
| `notes` | `notes` |
| `meetingManagersNotes` | `meeting_managers_notes` |
| `meetingManagersNotesSuite` | `meeting_managers_notes_suite` |
| `meetingManagersNotesEnd` | `meeting_managers_notes_end` |
| `internalNotes` | `internal_notes` |
| `neededFollowUp` | `needed_follow_up` |
| `providedFollowUp` | `provided_follow_up` |
| `marginalNotes` | `marginal_notes` |
| `observations` | `observations` |
| `templateUsingGroups` | `template_using_groups` |
| `meetingTransitionInsertingMe` | `meeting_transition_inserting_me` |
| `itemAssembly` | `item_assembly` |
| `itemAssemblyExcused` | `item_assembly_excused` |
| `itemAssemblyAbsents` | `item_assembly_absents` |
| `itemAssemblyGuests` | `item_assembly_guests` |
| `itemSignatures` | `item_signatures` |
| `copyGroups` | `copy_groups` |
| `restrictedCopyGroups` | `restricted_copy_groups` |
| `pollType` | `poll_type` |
| `pollTypeObservations` | `poll_type_observations` |
| `committeeObservations` | `committee_observations` |
| `committeeTranscript` | `committee_transcript` |
| `votesObservations` | `votes_observations` |
| `manuallyLinkedItems` | `manually_linked_items` |
| `otherMeetingConfigsClonableTo` | `other_meeting_configs_clonable_to` |
| `otherMeetingConfigsClonableToEmergency` | `other_meeting_configs_clonable_to_emergency` |
| `otherMeetingConfigsClonableToPrivacy` | `other_meeting_configs_clonable_to_privacy` |
| `otherMeetingConfigsClonableToFieldTitle` | `other_meeting_configs_clonable_to_field_title` |
| `otherMeetingConfigsClonableToFieldDescription` | `other_meeting_configs_clonable_to_field_description` |
| `otherMeetingConfigsClonableToFieldDetailedDescription` | `other_meeting_configs_clonable_to_field_detailed_description` |
| `otherMeetingConfigsClonableToFieldMotivation` | `other_meeting_configs_clonable_to_field_motivation` |
| `otherMeetingConfigsClonableToFieldDecision` | `other_meeting_configs_clonable_to_field_decision` |
| `otherMeetingConfigsClonableToFieldDecisionSuite` | `other_meeting_configs_clonable_to_field_decision_suite` |
| `otherMeetingConfigsClonableToFieldDecisionEnd` | `other_meeting_configs_clonable_to_field_decision_end` |
| `isAcceptableOutOfMeeting` | `is_acceptable_out_of_meeting` |
| `sendToAuthority` | `send_to_authority` |
| `privacy` | `privacy` |
| `completeness` | `completeness` |
| `itemIsSigned` | `item_is_signed` |
| `takenOverBy` | `taken_over_by` |
| `textCheckList` | `text_check_list` |

## AT widget `condition=` expressions (deferred to B.2.x)

Dexterity has no schema-level equivalent to AT's per-field
`condition="python: …"` widget hook. The DX schema in
`content/meetingitem.py` preserves each AT condition as a comment above
the field; concretely, the equivalent runtime visibility logic will be
moved to:

- `form.mode(...)` directives evaluated at form-rendering time
  (when the predicate depends only on schema/permissions), or
- A custom edit form / view layer (when the predicate calls
  ``here.attribute_is_used(...)``, ``here.adapted().show_field(...)``,
  ``here.showOptionalAdvisers()``, etc.).

The vast majority of conditions match three patterns:

- `here.attribute_is_used('<field>')` — driven by
  `MeetingConfig.used_item_attributes`. Will be lifted into the edit
  form's ``updateFields`` / ``updateWidgets``.
- `here.adapted().show_field('<field>')` — for the new follow-up /
  groups-in-charge-notes fields. Same pattern.
- Permission-style conditions (``here.showOralQuestion``,
  ``here.showItemIsSigned``, ``here.adapted().mayChangeListType``)
  — translate to write-permission checks where possible, otherwise
  remain as form-level logic.

## Default values: AT `default_method` → DX `defaultFactory`

Three fields use `default_method=` in AT and need a `defaultFactory`
binding in DX:

| Field | AT method | Status |
|---|---|---|
| `budget_infos` | `getDefaultBudgetInfo` | TODO B.2.x |
| `to_discuss` | `getDefaultToDiscuss` | TODO B.2.x |
| `poll_type` | `getDefaultPollType` | TODO B.2.x |

For B.2.0 the schema declares these without a default (or with a safe
constant) — no semantic regression while AT remains the active class.

## Vocabularies

Most AT fields already use `vocabulary_factory='Products.PloneMeeting.vocabularies.<name>'`,
which the DX schema can reuse verbatim. The fields that originally
used `vocabulary='listFoo'` (AT instance method) are now wired to
`IVocabularyFactory` factories — added in **B.2.1**:

| AT method | DX vocabulary name | Source (B.2.1) |
|---|---|---|
| `listCategories` | `Products.PloneMeeting.vocabularies.categoriesvocabulary` | reuse pre-existing `ItemCategoriesVocabulary` |
| `listClassifiers` | `Products.PloneMeeting.vocabularies.classifiersvocabulary` | reuse pre-existing `ItemClassifiersVocabulary` |
| `listEmergencies` | `Products.PloneMeeting.vocabularies.item_emergencies_vocabulary` | new `ItemEmergenciesVocabulary` |
| `listMeetingsAcceptingItems` | `Products.PloneMeeting.vocabularies.item_meetings_accepting_items_vocabulary` | new `ItemMeetingsAcceptingItemsVocabulary` |
| `listItemTags` | `Products.PloneMeeting.vocabularies.item_tags_vocabulary` | new `ItemTagsVocabulary` |
| `listItemInitiators` | `Products.PloneMeeting.vocabularies.item_initiators_vocabulary` | new `ItemInitiatorsVocabulary` |
| `listMeetingTransitions` (item-side) | `Products.PloneMeeting.vocabularies.item_meeting_transitions_vocabulary` | new `ItemMeetingTransitionsVocabulary` (distinct from cfg-side `MeetingTransitionsVocabulary`) |
| `listCompleteness` | `Products.PloneMeeting.vocabularies.item_completeness_vocabulary` | new `ItemCompletenessVocabulary` |

## Permissions

| Permission constant | AT fields | DX fields |
|---|---|---|
| `ReadBudgetInfos` | `budgetRelated`, `budgetInfos` | `budget_related`, `budget_infos` |
| `WriteBudgetInfos` | `budgetRelated`, `budgetInfos` | `budget_related`, `budget_infos` |
| `WriteDecision` | `emergencyMotivation`, `motivation`, `decision`, `decisionSuite`, `decisionEnd`, `otherMeetingConfigsClonableToFieldMotivation`, `otherMeetingConfigsClonableToFieldDecision`, `otherMeetingConfigsClonableToFieldDecisionSuite`, `otherMeetingConfigsClonableToFieldDecisionEnd` | snake_case equivalents |
| `WriteMarginalNotes` | `votesResult` (write), `marginalNotes` (write) | `votes_result`, `marginal_notes` |
| `WriteItemMeetingManagerFields` | `inAndOutMoves`, `notes`, `meetingManagersNotes`, `meetingManagersNotesSuite`, `meetingManagersNotesEnd`, `restrictedCopyGroups`, `observations`, `pollTypeObservations`, `votesObservations`, `textCheckList` | snake_case equivalents |
| `WriteInternalNotes` (read+write) | `internalNotes` | `internal_notes` |
| `WriteCommitteeFields` | `committeeObservations`, `committeeTranscript` | `committee_observations`, `committee_transcript` |
| `View` (write) | `groupsInChargeNotes`, `neededFollowUp`, `providedFollowUp` | snake_case equivalents |
| `'PloneMeeting: Read decision'` | `emergencyMotivation`, `motivation`, `decision`, `decisionSuite`, `decisionEnd`, `votesResult`, `otherMeetingConfigsClonableToField{Motivation,Decision,DecisionSuite,DecisionEnd}` | snake_case equivalents |
| `'PloneMeeting: Read item observations'` | `observations` | `observations` |

In DX the `read_permission` / `write_permission` directives are applied
via `plone.autoform.directives.form.read_permission(...)` /
`form.write_permission(...)` rather than as keyword arguments to the
field constructor.

## Schema caveats

- **`manuallyLinkedItems`** was an AT `ReferenceField(relationship='ManuallyLinkedItem',
  multiValued=True)`. In B.2.0 the DX schema declares it as a plain
  `schema.List(value_type=schema.TextLine())` of UID strings. B.2.x
  will switch to `z3c.relationfield.schema.RelationList` once the FTI
  swap lands and we can wire `IObjectAdded` / `IObjectModified` to
  rebuild the relation catalog.
- **`description`** keeps its AT name; we deliberately do not rely on
  the `IDublinCore.description` behavior (the FTI does not include it),
  so there is no namespace collision.
- **`text_check_list`, `item_assembly*`, `item_signatures`** were
  `TextField(allowable_content_types=('text/plain',))` with a
  `TextAreaWidget`. They are declared as `schema.Text` in DX; the
  textarea widget assignment will land with the form/view migration in
  B.2.5.
- **`other_meeting_configs_clonable_to_field_title`**: AT enforced
  `maxlength=750` on the widget; DX uses `max_length=750` on the
  `schema.TextLine` (validated server-side, not just at the widget
  layer).
- **`item_number`, `item_reference`** are declared `form.mode('hidden')`
  — they are computed server-side and never user-editable, mirroring
  `widget=…(visible=False)` on the AT side.

## Removed during B.2.x (placeholder)

To be filled in as the AT class is dismantled. Categories that will
appear here, mirroring `MIGRATION_SUMMARY_MEETINGCONFIG.md`:

- `registerType(MeetingItem, PROJECTNAME)` at the end of
  `MeetingItem.py` (B.2.8).
- AT `at_post_create_script` / `at_post_edit_script` stubs (move to
  `IObjectAdded` / `IObjectModified` subscribers in `events.zcml`,
  B.2.1).
- `_at_creation_flag` / `_at_rename_after_creation` references in
  callers (B.2.8).
- Any orphaned `security.declarePrivate('listX')` declarations once
  the corresponding AT method is removed (B.2.8).

## Impacted files (callers needing update)

Generated via grep of the AT accessor patterns; not every match is an
accessor — inspect each file. Will be elaborated phase by phase.

**Core modules:**

- `MeetingItem.py` (the AT class itself — purged in B.2.8)
- `MeetingConfig.py`
- `Meeting.py`
- `ToolPloneMeeting.py`
- `adapters.py`
- `events.py`
- `indexes.py`
- `utils.py`
- `validators.py`
- `vocabularies.py`
- `columns.py`
- `model/adaptations.py`

**Browser layer:**

- `browser/views.py`
- `browser/overrides.py`
- `browser/advices.py`
- `browser/annexes.py`
- `browser/itemvotes.py`
- `browser/itemattendee.py`
- `browser/itemassembly.py`
- `browser/batchactions.py`
- `browser/portlet_todo.py`
- `browser/viewlets.py`

**Other modules:**

- `content/advice.py`
- `content/meeting.py`
- `content/meetingconfig.py` (already DX — but holds business methods
  that walk into `MeetingItem` via `getXxx()`)
- `documentgenerator/condition.py`
- `etags.py`
- `exportimport/content.py`
- `external/views.py`
- `filters/css_transforms.py`
- `ftw_labels/adapters.py`
- `ftw_labels/overrides.py`

⚠️ Templates (`.pt` files in `browser/templates/` and
`skins/plonemeeting_templates/`) reference field names via
`context/getXxx`, `here/xxx` TALES expressions — grep both directories
for the old camelCase names.

⚠️ Sub-packages (`plonemeeting.restapi`, profile packages
`Products.MeetingCommunes` and friends, `imio.zamqp.pm`,
`imio.dms.mail`) may also have accessor calls — audit those separately.

## Event wiring

| Event | Phase | DX subscriber |
|---|---|---|
| Object added | **landed B.2.1** | `.content.meetingitem.IMeetingItem` ↔ `zope.lifecycleevent.IObjectAddedEvent` → `events.onItemInitialized` |
| Object modified | n/a | `.interfaces.IMeetingItem` ↔ `IObjectModifiedEvent` → `events.onItemModified` (already exists, fires for DX too via marker iface inheritance) |
| Object will be removed | n/a | `.interfaces.IMeetingItem` (already exists, schema iface extends marker, parent subscribers still apply) |

The DX schema interface `content.meetingitem.IMeetingItem` extends the
existing marker `interfaces.IMeetingItem`, so all existing subscribers
wired to the marker automatically apply to DX instances. The B.2.1
addition specifically targets ``IObjectAddedEvent`` because the AT
``IObjectInitializedEvent`` has no DX counterpart — without the new
subscriber, ``onItemInitialized`` would not run on DX item creation.

## View migration (planned, B.2.5)

The legacy AT skin-layer templates `skins/plonemeeting_templates/meetingitem_view.pt`
and `skins/plonemeeting_templates/meetingitem_edit.pt` rely on
`here.Schemata()`, `here.getField(...)` and `here/widgets/field/macros/{view,edit}` —
all of which are unavailable on Dexterity objects.

Replacement plan (mirroring the MeetingConfig recipe):
- `browser/meetingitem.py::MeetingItemView(DefaultView)`, registered as
  `name="view"` for `Products.PloneMeeting.interfaces.IMeetingItem`.
- DX field widgets rendered via `view.widgets` (backed by
  `DefaultView`).
- The bulk of `meetingitem_view.pt` consists of conditional widget
  rendering keyed on `attribute_is_used(...)` — this collapses naturally
  to `form.mode` directives plus a small `updateWidgets` override.
