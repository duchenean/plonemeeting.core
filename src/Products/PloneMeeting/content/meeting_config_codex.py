# -*- coding: utf-8 -*-

import copy

from collective.z3cform.datagridfield import DataGridField
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.supermodel import model
from Products.PloneMeeting.config import PMMessageFactory as _
from Products.PloneMeeting.config import WriteRiskyConfig
from Products.PloneMeeting.interfaces import IConfigElement
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.orderedselect import OrderedSelectFieldWidget
from z3c.form.browser.select import SelectFieldWidget
from z3c.form.browser.textarea import TextAreaFieldWidget
from zope import schema
from zope.interface import Interface


defValues = MeetingConfigDescriptor.get()


def _default_value(attribute_name):
    """Return a fresh copy of a MeetingConfigDescriptor default."""
    def default_factory():
        return copy.deepcopy(getattr(defValues, attribute_name))
    return default_factory


class ICertifiedSignaturesRowSchema(Interface):
    """Row schema for MeetingConfig.certifiedSignatures."""

    form.widget('signature_number', SelectFieldWidget)
    signature_number = schema.Choice(
        title=_(
            u"title_meeting_config_certified_signatures_signature_number",
            default=u"Certified signatures signature number",
        ),
        description=_(
            u"desc_meeting_config_certified_signatures_signature_number",
            default=u"Select the signature number, keep signatures ordered by number.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_numbers",
        required=False,
    )

    name = schema.TextLine(
        title=_(u"title_meeting_config_certified_signatures_name", default=u"Certified signatures signatory name"),
        description=_(
            u"desc_meeting_config_certified_signatures_name",
            default=u"Name of the signatory (for example 'Mister John Doe').",
        ),
        required=False,
    )

    function = schema.TextLine(
        title=_(
            u"title_meeting_config_certified_signatures_function",
            default=u"Certified signatures signatory function",
        ),
        description=_(
            u"desc_meeting_config_certified_signatures_function",
            default=u"Function of the signatory (for example 'Mayor').",
        ),
        required=False,
    )

    form.widget('held_position', SelectFieldWidget)
    held_position = schema.Choice(
        title=_(
            u"title_meeting_config_certified_signatures_held_position",
            default=u"Certified signatures held position",
        ),
        description=_(
            u"desc_meeting_config_certified_signatures_held_position",
            default=(
                u"Select a held position if necessary, 'Name', 'Function' and other data of this held position will "
                u"be used if you leave 'Name' and 'Function' columns empty."
            ),
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_contacts",
        required=False,
    )

    date_from = schema.TextLine(
        title=_(
            u"title_meeting_config_certified_signatures_date_from",
            default=u"Certified signatures valid from (included)",
        ),
        description=_(
            u"desc_meeting_config_certified_signatures_date_from",
            default=u"Enter valid from date, use following format : YYYY/MM/DD, leave empty so it is always valid.",
        ),
        required=False,
    )

    date_to = schema.TextLine(
        title=_(
            u"title_meeting_config_certified_signatures_date_to",
            default=u"Certified signatures valid to (included)",
        ),
        description=_(
            u"desc_meeting_config_certified_signatures_date_to",
            default=u"Enter valid to date, use following format : YYYY/MM/DD, leave empty so it is always valid.",
        ),
        required=False,
    )



class IInsertingMethodsOnAddItemRowSchema(Interface):
    """Row schema for MeetingConfig.insertingMethodsOnAddItem."""

    form.widget('inserting_method', SelectFieldWidget)
    inserting_method = schema.Choice(
        title=_(u"title_meeting_config_inserting_methods_on_add_item_inserting_method", default=u"Inserting method"),
        description=_(
            u"desc_meeting_config_inserting_methods_on_add_item_inserting_method",
            default=(
                u"Select the inserting method, methods will be applied in given order, you can not select twice same "
                u"inserting method."
            ),
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_inserting_methods",
        required=False,
    )

    form.widget('reverse', SelectFieldWidget)
    reverse = schema.Choice(
        title=_(u"title_meeting_config_inserting_methods_on_add_item_reverse", default=u"Reverse inserting method?"),
        description=_(
            u"desc_meeting_config_inserting_methods_on_add_item_reverse",
            default=u"Reverse order of selected inserting method?",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )



class IListTypesRowSchema(Interface):
    """Row schema for MeetingConfig.listTypes."""

    identifier = schema.TextLine(
        title=_(u"title_meeting_config_list_types_identifier", default=u"List type identifier"),
        description=_(
            u"desc_meeting_config_list_types_identifier",
            default=u"Enter an internal identifier, use only lowercase letters.",
        ),
        required=False,
    )

    label = schema.TextLine(
        title=_(u"title_meeting_config_list_types_label", default=u"List type label"),
        description=_(
            u"desc_meeting_config_list_types_label",
            default=(
                u"Enter a short label that will be displayed in the application.  This will be translated by the "
                u"application if possible.  If you want to colorize this new list type on the meeting view, you will "
                u"need to do this using CSS like it is the case for 'late' items."
            ),
        ),
        required=False,
    )

    used_in_inserting_method = schema.Bool(
        title=_(
            u"title_meeting_config_list_types_used_in_inserting_method",
            default=u"List type used_in_inserting_method",
        ),
        description=_(
            u"desc_meeting_config_list_types_used_in_inserting_method",
            default=(
                u"If the inserting method \"on list types\" is used, will this list type be taken into account while "
                u"inserting the item in the meeting?"
            ),
        ),
        required=False,
    )



class IMeetingConfigsToCloneToRowSchema(Interface):
    """Row schema for MeetingConfig.meetingConfigsToCloneTo."""

    form.widget('meeting_config', SelectFieldWidget)
    meeting_config = schema.Choice(
        title=_(
            u"title_meeting_config_meeting_configs_to_clone_to_meeting_config",
            default=u"Meeting config to clone to Meeting config",
        ),
        description=_(
            u"desc_meeting_config_meeting_configs_to_clone_to_meeting_config",
            default=u"The meeting config the item of this meeting config will be sendable to.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_configs_to_clone_to",
        required=False,
    )

    form.widget('trigger_workflow_transitions_until', SelectFieldWidget)
    trigger_workflow_transitions_until = schema.Choice(
        title=_(
            u"title_meeting_config_meeting_configs_to_clone_to_trigger_workflow_transitions_until",
            default=u"Meeting config to clone to Trigger workflow transitions until",
        ),
        description=_(
            u"desc_meeting_config_meeting_configs_to_clone_to_trigger_workflow_transitions_until",
            default=(
                u"While sent, the new item is in the workflow initial state, if it was sent automatically (depending "
                u"on states selected in field 'States in which an item will be automatically sent to selected other "
                u"meeting configurations' here under), some transitions can be automatically triggered for the new "
                u"item, select until which transition it will be done (selected transition will also be triggered).  "
                u"This relies on the 'Transitions for presenting an item' you defined in the 'Workflows' tab of the "
                u"meeting configuration the item will be sent to."
            ),
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_transitions_until_presented",
        required=False,
    )



class ICssTransformsRowSchema(Interface):
    """Row schema for MeetingConfig.cssTransforms."""

    css_class = schema.TextLine(
        title=_(u"title_meeting_config_css_transforms_css_class", default=u"Css transform css class"),
        description=_(u"desc_meeting_config_css_transforms_css_class", default=u"Css transform css class descr"),
        required=False,
    )

    form.widget('action', SelectFieldWidget)
    action = schema.Choice(
        title=_(u"title_meeting_config_css_transforms_action", default=u"Css transform action"),
        description=_(u"desc_meeting_config_css_transforms_action", default=u"Css transform action descr"),
        vocabulary=u"ConfigCssTransformsActions",
        required=False,
    )

    replace_new_content = schema.TextLine(
        title=_(
            u"title_meeting_config_css_transforms_replace_new_content",
            default=u"Css transform replace new content",
        ),
        description=_(
            u"desc_meeting_config_css_transforms_replace_new_content",
            default=u"Css transform replace new content descr",
        ),
        required=False,
    )

    replace_new_css_class = schema.TextLine(
        title=_(
            u"title_meeting_config_css_transforms_replace_new_css_class",
            default=u"Css transform replace new css class",
        ),
        description=_(
            u"desc_meeting_config_css_transforms_replace_new_css_class",
            default=u"Css transform replace new css class descr",
        ),
        required=False,
    )

    form.widget('powerobservers', CheckBoxFieldWidget)
    powerobservers = schema.List(
        title=_(u"title_meeting_config_css_transforms_powerobservers", default=u"Css transform powerobservers"),
        description=_(
            u"desc_meeting_config_css_transforms_powerobservers",
            default=u"Css transform powerobservers descr",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_power_observers_types",
        ),
        required=False,
    )



class IItemWfValidationLevelsRowSchema(Interface):
    """Row schema for MeetingConfig.itemWFValidationLevels."""

    state = schema.TextLine(
        title=_(u"title_meeting_config_item_wf_validation_levels_state", default=u"Item WF validation levels state"),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_state",
            default=u"Item WF validation levels state description.",
        ),
        required=True,
    )

    state_title = schema.TextLine(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_state_title",
            default=u"Item WF validation levels state title",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_state_title",
            default=u"Item WF validation levels state title description.",
        ),
        required=True,
    )

    leading_transition = schema.TextLine(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_leading_transition",
            default=u"Item WF validation levels leading transition",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_leading_transition",
            default=u"Item WF validation levels leading transition description.",
        ),
        required=True,
    )

    leading_transition_title = schema.TextLine(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_leading_transition_title",
            default=u"Item WF validation levels leading transition title",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_leading_transition_title",
            default=u"Item WF validation levels leading transition title description.",
        ),
        required=True,
    )

    back_transition = schema.TextLine(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_back_transition",
            default=u"Item WF validation levels back transition",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_back_transition",
            default=u"Item WF validation levels back transition description.",
        ),
        required=True,
    )

    back_transition_title = schema.TextLine(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_back_transition_title",
            default=u"Item WF validation levels back transition title",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_back_transition_title",
            default=u"Item WF validation levels back transition title description.",
        ),
        required=True,
    )

    form.widget('suffix', SelectFieldWidget)
    suffix = schema.Choice(
        title=_(u"title_meeting_config_item_wf_validation_levels_suffix", default=u"Item WF validation levels suffix"),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_suffix",
            default=u"Item WF validation levels suffix description.",
        ),
        vocabulary=u"collective.contact.plonegroup.functions",
        default=u"1",
        required=False,
    )

    form.widget('extra_suffixes', CheckBoxFieldWidget)
    extra_suffixes = schema.List(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_extra_suffixes",
            default=u"Item WF validation levels extra suffixes",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_extra_suffixes",
            default=u"Item WF validation levels extra suffixes description.",
        ),
        value_type=schema.Choice(
            vocabulary=u"collective.contact.plonegroup.functions",
        ),
        required=False,
    )

    form.widget('enabled', SelectFieldWidget)
    enabled = schema.Choice(
        title=_(
            u"title_meeting_config_item_wf_validation_levels_enabled",
            default=u"Item WF validation levels enabled",
        ),
        description=_(
            u"desc_meeting_config_item_wf_validation_levels_enabled",
            default=u"Item WF validation levels enabled description.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"1",
        required=False,
    )



class IOnTransitionFieldTransformsRowSchema(Interface):
    """Row schema for MeetingConfig.onTransitionFieldTransforms."""

    form.widget('transition', SelectFieldWidget)
    transition = schema.Choice(
        title=_(
            u"title_meeting_config_on_transition_field_transforms_transition",
            default=u"On transition field transform transition",
        ),
        description=_(
            u"desc_meeting_config_on_transition_field_transforms_transition",
            default=u"The transition that will trigger the field transform.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_transitions",
        required=False,
    )

    form.widget('field_name', SelectFieldWidget)
    field_name = schema.Choice(
        title=_(
            u"title_meeting_config_on_transition_field_transforms_field_name",
            default=u"On transition field transform field name",
        ),
        description=_(
            u"desc_meeting_config_on_transition_field_transforms_field_name",
            default=u"The item field that will be transformed.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_rich_text_fields",
        required=False,
    )

    tal_expression = schema.TextLine(
        title=_(
            u"title_meeting_config_on_transition_field_transforms_tal_expression",
            default=u"On transition field transform TAL expression",
        ),
        description=_(
            u"desc_meeting_config_on_transition_field_transforms_tal_expression",
            default=(
                u"The TAL expression.  Element 'here' represent the item.  This expression MUST return valid HTML or "
                u"it will not behave properly on the item."
            ),
        ),
        required=False,
    )



class IOnMeetingTransitionItemActionToExecuteRowSchema(Interface):
    """Row schema for MeetingConfig.onMeetingTransitionItemActionToExecute."""

    form.widget('meeting_transition', SelectFieldWidget)
    meeting_transition = schema.Choice(
        title=_(
            u"title_meeting_config_on_meeting_transition_item_action_to_execute_meeting_transition",
            default=u"On meeting transition item action to execute meeting transition",
        ),
        description=_(
            u"desc_meeting_config_on_meeting_transition_item_action_to_execute_meeting_transition",
            default=u"The transition triggered on the meeting.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_transitions",
        required=False,
    )

    form.widget('item_action', SelectFieldWidget)
    item_action = schema.Choice(
        title=_(
            u"title_meeting_config_on_meeting_transition_item_action_to_execute_item_action",
            default=u"On meeting transition item action to execute item action",
        ),
        description=_(
            u"desc_meeting_config_on_meeting_transition_item_action_to_execute_item_action",
            default=u"The action that will be executed on every items of the meeting.",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_executable_item_actions",
        required=False,
    )

    tal_expression = schema.TextLine(
        title=_(
            u"title_meeting_config_on_meeting_transition_item_action_to_execute_tal_expression",
            default=u"On meeting transition item action to execute tal expression",
        ),
        description=_(
            u"desc_meeting_config_on_meeting_transition_item_action_to_execute_tal_expression",
            default=u"The action to execute when 'Execute given action' is selected in column 'Item action'.",
        ),
        required=False,
    )



class ICustomAdvisersRowSchema(Interface):
    """Row schema for MeetingConfig.customAdvisers."""

    form.omitted('row_id')
    row_id = schema.TextLine(
        title=_(u"title_meeting_config_custom_advisers_row_id", default=u"Custom adviser row id"),
        required=False,
    )

    form.widget('org', SelectFieldWidget)
    org = schema.Choice(
        title=_(u"title_meeting_config_custom_advisers_org", default=u"Custom adviser organization"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_active_orgs_for_custom_advisers",
        required=False,
    )

    gives_auto_advice_on = schema.TextLine(
        title=_(
            u"title_meeting_config_custom_advisers_gives_auto_advice_on",
            default=u"Custom adviser gives automatic advice on",
        ),
        description=_(
            u"desc_meeting_config_custom_advisers_gives_auto_advice_on",
            default=u"gives_auto_advice_on_col_description",
        ),
        required=False,
    )

    gives_auto_advice_on_help_message = schema.TextLine(
        title=_(
            u"title_meeting_config_custom_advisers_gives_auto_advice_on_help_message",
            default=u"Custom adviser gives automatic advice on help message",
        ),
        description=_(
            u"desc_meeting_config_custom_advisers_gives_auto_advice_on_help_message",
            default=u"gives_auto_advice_on_help_message_col_description",
        ),
        required=False,
    )

    for_item_created_from = schema.TextLine(
        title=_(
            u"title_meeting_config_custom_advisers_for_item_created_from",
            default=u"Rule activated for item created from",
        ),
        description=_(
            u"desc_meeting_config_custom_advisers_for_item_created_from",
            default=u"for_item_created_from_col_description",
        ),
        default=u"DateTime().strftime('%Y/%m/%d')",
        required=True,
    )

    for_item_created_until = schema.TextLine(
        title=_(
            u"title_meeting_config_custom_advisers_for_item_created_until",
            default=u"Rule activated for item created until",
        ),
        description=_(
            u"desc_meeting_config_custom_advisers_for_item_created_until",
            default=u"for_item_created_until_col_description",
        ),
        required=False,
    )

    delay = schema.TextLine(
        title=_(u"title_meeting_config_custom_advisers_delay", default=u"Delay for giving advice"),
        description=_(u"desc_meeting_config_custom_advisers_delay", default=u"delay_col_description"),
        required=False,
    )

    delay_left_alert = schema.TextLine(
        title=_(u"title_meeting_config_custom_advisers_delay_left_alert", default=u"Delay left alert"),
        description=_(
            u"desc_meeting_config_custom_advisers_delay_left_alert",
            default=u"delay_left_alert_col_description",
        ),
        required=False,
    )

    delay_label = schema.TextLine(
        title=_(u"title_meeting_config_custom_advisers_delay_label", default=u"Custom adviser delay label"),
        description=_(u"desc_meeting_config_custom_advisers_delay_label", default=u"delay_label_col_description"),
        required=False,
    )

    form.widget('is_delay_calendar_days', SelectFieldWidget)
    is_delay_calendar_days = schema.Choice(
        title=_(
            u"title_meeting_config_custom_advisers_is_delay_calendar_days",
            default=u"Is delay computed in calendar days?",
        ),
        description=_(
            u"desc_meeting_config_custom_advisers_is_delay_calendar_days",
            default=u"is_delay_calendar_days_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )

    available_on = schema.TextLine(
        title=_(u"title_meeting_config_custom_advisers_available_on", default=u"Available on"),
        description=_(u"desc_meeting_config_custom_advisers_available_on", default=u"available_on_col_description"),
        required=False,
    )

    form.widget('is_linked_to_previous_row', SelectFieldWidget)
    is_linked_to_previous_row = schema.Choice(
        title=_(
            u"title_meeting_config_custom_advisers_is_linked_to_previous_row",
            default=u"Is linked to previous row?",
        ),
        description=_(
            u"desc_meeting_config_custom_advisers_is_linked_to_previous_row",
            default=u"Is linked to previous row description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )



class IPowerObserversRowSchema(Interface):
    """Row schema for MeetingConfig.powerObservers."""

    form.omitted('row_id')
    row_id = schema.TextLine(
        title=_(u"title_meeting_config_power_observers_row_id", default=u"Power observer row id"),
        required=False,
    )

    label = schema.TextLine(
        title=_(u"title_meeting_config_power_observers_label", default=u"Power observer label"),
        description=_(u"desc_meeting_config_power_observers_label", default=u"power_observers_label_col_description"),
        required=True,
    )

    form.widget('item_states', CheckBoxFieldWidget)
    item_states = schema.List(
        title=_(u"title_meeting_config_power_observers_item_states", default=u"Power observer item viewable states"),
        description=_(
            u"desc_meeting_config_power_observers_item_states",
            default=u"power_observers_item_states_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        required=False,
    )

    item_access_on = schema.TextLine(
        title=_(
            u"title_meeting_config_power_observers_item_access_on",
            default=u"Power observer item access TAL expression",
        ),
        description=_(
            u"desc_meeting_config_power_observers_item_access_on",
            default=u"power_observers_item_access_on_col_description",
        ),
        required=False,
    )

    form.widget('meeting_states', CheckBoxFieldWidget)
    meeting_states = schema.List(
        title=_(
            u"title_meeting_config_power_observers_meeting_states",
            default=u"Power observer meeting viewable states",
        ),
        description=_(
            u"desc_meeting_config_power_observers_meeting_states",
            default=u"power_observers_meeting_states_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_states",
        ),
        required=False,
    )

    meeting_access_on = schema.TextLine(
        title=_(
            u"title_meeting_config_power_observers_meeting_access_on",
            default=u"Power observer meeting access TAL expression",
        ),
        description=_(
            u"desc_meeting_config_power_observers_meeting_access_on",
            default=u"power_observers_meeting_access_on_col_description",
        ),
        required=False,
    )



class ILabelsConfigRowSchema(Interface):
    """Row schema for MeetingConfig.labelsConfig."""

    form.widget('label_id', SelectFieldWidget)
    label_id = schema.Choice(
        title=_(u"title_meeting_config_labels_config_label_id", default=u"Labels config label id"),
        description=_(u"desc_meeting_config_labels_config_label_id", default=u"labels_config_label_id_col_description"),
        vocabulary=u"Products.PloneMeeting.vocabularies.configftwlabelsvocabulary",
        required=False,
    )

    form.widget('view_groups', CheckBoxFieldWidget)
    view_groups = schema.List(
        title=_(u"title_meeting_config_labels_config_view_groups", default=u"Labels config view groups"),
        description=_(
            u"desc_meeting_config_labels_config_view_groups",
            default=u"labels_config_view_groups_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=(
                u"Products.PloneMeeting.vocabularies."
                u"meeting_config_list_item_attribute_visible_for_with_meeting_managers"
            ),
        ),
        required=False,
    )

    form.widget('view_groups_excluding', SelectFieldWidget)
    view_groups_excluding = schema.Choice(
        title=_(
            u"title_meeting_config_labels_config_view_groups_excluding",
            default=u"Labels config view groups excluding",
        ),
        description=_(
            u"desc_meeting_config_labels_config_view_groups_excluding",
            default=u"labels_config_view_groups_excluding_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )

    form.widget('view_states', CheckBoxFieldWidget)
    view_states = schema.List(
        title=_(u"title_meeting_config_labels_config_view_states", default=u"Labels config view states"),
        description=_(
            u"desc_meeting_config_labels_config_view_states",
            default=u"labels_config_view_states_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        required=False,
    )

    view_access_on = schema.TextLine(
        title=_(
            u"title_meeting_config_labels_config_view_access_on",
            default=u"Labels config view access TAL expression",
        ),
        description=_(
            u"desc_meeting_config_labels_config_view_access_on",
            default=u"labels_config_view_access_on_col_description",
        ),
        required=False,
    )

    form.widget('view_access_on_cache', SelectFieldWidget)
    view_access_on_cache = schema.Choice(
        title=_(
            u"title_meeting_config_labels_config_view_access_on_cache",
            default=u"Labels config view access TAL expression cache",
        ),
        description=_(
            u"desc_meeting_config_labels_config_view_access_on_cache",
            default=u"labels_config_view_access_on_cache_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"1",
        required=False,
    )

    form.widget('edit_groups', CheckBoxFieldWidget)
    edit_groups = schema.List(
        title=_(u"title_meeting_config_labels_config_edit_groups", default=u"Labels config edit groups"),
        description=_(
            u"desc_meeting_config_labels_config_edit_groups",
            default=u"labels_config_edit_groups_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=(
                u"Products.PloneMeeting.vocabularies."
                u"meeting_config_list_item_attribute_visible_for_with_meeting_managers"
            ),
        ),
        required=False,
    )

    form.widget('edit_groups_excluding', SelectFieldWidget)
    edit_groups_excluding = schema.Choice(
        title=_(
            u"title_meeting_config_labels_config_edit_groups_excluding",
            default=u"Labels config edit groups excluding",
        ),
        description=_(
            u"desc_meeting_config_labels_config_edit_groups_excluding",
            default=u"labels_config_edit_groups_excluding_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )

    form.widget('edit_states', CheckBoxFieldWidget)
    edit_states = schema.List(
        title=_(u"title_meeting_config_labels_config_edit_states", default=u"Labels config edit states"),
        description=_(
            u"desc_meeting_config_labels_config_edit_states",
            default=u"labels_config_edit_states_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        required=False,
    )

    edit_access_on = schema.TextLine(
        title=_(
            u"title_meeting_config_labels_config_edit_access_on",
            default=u"Labels config edit access TAL expression",
        ),
        description=_(
            u"desc_meeting_config_labels_config_edit_access_on",
            default=u"labels_config_edit_access_on_col_description",
        ),
        required=False,
    )

    form.widget('edit_access_on_cache', SelectFieldWidget)
    edit_access_on_cache = schema.Choice(
        title=_(
            u"title_meeting_config_labels_config_edit_access_on_cache",
            default=u"Labels config edit access TAL expression cache",
        ),
        description=_(
            u"desc_meeting_config_labels_config_edit_access_on_cache",
            default=u"labels_config_edit_access_on_cache_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"1",
        required=False,
    )

    form.widget('update_local_roles', SelectFieldWidget)
    update_local_roles = schema.Choice(
        title=_(u"title_meeting_config_labels_config_update_local_roles", default=u"Labels config update local roles?"),
        description=_(
            u"desc_meeting_config_labels_config_update_local_roles",
            default=u"labels_config_update_local_roles_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )



class IItemFieldsConfigRowSchema(Interface):
    """Row schema for MeetingConfig.itemFieldsConfig."""

    form.widget('name', SelectFieldWidget)
    name = schema.Choice(
        title=_(u"title_meeting_config_item_fields_config_name", default=u"Item fields config name"),
        description=_(u"desc_meeting_config_item_fields_config_name", default=u"item_fields_config_name_description"),
        vocabulary=u"Products.PloneMeeting.vocabularies.item_fields_config_vocabulary",
        required=False,
    )

    view = schema.TextLine(
        title=_(u"title_meeting_config_item_fields_config_view", default=u"Item fields config view TAL expression"),
        description=_(
            u"desc_meeting_config_item_fields_config_view",
            default=u"item_fields_config_view_tal_expr_description",
        ),
        required=False,
    )

    edit = schema.TextLine(
        title=_(u"title_meeting_config_item_fields_config_edit", default=u"Item fields config edit TAL expression"),
        description=_(
            u"desc_meeting_config_item_fields_config_edit",
            default=u"item_fields_config_edit_tal_expr_description",
        ),
        required=False,
    )



class ICommitteesRowSchema(Interface):
    """Row schema for MeetingConfig.committees."""

    form.omitted('row_id')
    row_id = schema.TextLine(
        title=_(u"title_meeting_config_committees_row_id", default=u"Committee row id"),
        required=False,
    )

    label = schema.TextLine(
        title=_(u"title_meeting_config_committees_label", default=u"Committee label"),
        required=True,
    )

    acronym = schema.TextLine(
        title=_(u"title_meeting_config_committees_acronym", default=u"Committee acronym"),
        required=False,
    )

    default_place = schema.TextLine(
        title=_(u"title_meeting_config_committees_default_place", default=u"Committee default place"),
        description=_(
            u"desc_meeting_config_committees_default_place",
            default=u"committees_default_place_col_description",
        ),
        required=False,
    )

    form.widget('default_assembly', TextAreaFieldWidget)
    default_assembly = schema.Text(
        title=_(u"title_meeting_config_committees_default_assembly", default=u"Committee default assembly"),
        description=_(
            u"desc_meeting_config_committees_default_assembly",
            default=u"committees_default_assembly_col_description",
        ),
        required=False,
    )

    form.widget('default_signatures', TextAreaFieldWidget)
    default_signatures = schema.Text(
        title=_(u"title_meeting_config_committees_default_signatures", default=u"Committee default signatures"),
        description=_(
            u"desc_meeting_config_committees_default_signatures",
            default=u"committees_default_signatures_col_description",
        ),
        required=False,
    )

    form.widget('default_attendees', CheckBoxFieldWidget)
    default_attendees = schema.List(
        title=_(u"title_meeting_config_committees_default_attendees", default=u"Committee default attendees"),
        description=_(
            u"desc_meeting_config_committees_default_attendees",
            default=u"committees_default_attendees_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_committee_attendees",
        ),
        required=False,
    )

    form.widget('default_signatories', CheckBoxFieldWidget)
    default_signatories = schema.List(
        title=_(u"title_meeting_config_committees_default_signatories", default=u"Committee default signatories"),
        description=_(
            u"desc_meeting_config_committees_default_signatories",
            default=u"committees_default_signatories_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_committee_attendees",
        ),
        required=False,
    )

    form.widget('using_groups', CheckBoxFieldWidget)
    using_groups = schema.List(
        title=_(u"title_meeting_config_committees_using_groups", default=u"Committee using groups"),
        description=_(
            u"desc_meeting_config_committees_using_groups",
            default=u"committees_using_groups_col_description",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_proposing_groups",
        ),
        required=False,
    )

    form.widget('auto_from', CheckBoxFieldWidget)
    auto_from = schema.List(
        title=_(u"title_meeting_config_committees_auto_from", default=u"Committee auto from"),
        description=_(u"desc_meeting_config_committees_auto_from", default=u"committees_auto_from_col_description"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_committee_auto_from",
        ),
        required=False,
    )

    form.widget('supplements', SelectFieldWidget)
    supplements = schema.Choice(
        title=_(u"title_meeting_config_committees_supplements", default=u"Committee supplements"),
        description=_(u"desc_meeting_config_committees_supplements", default=u"committees_supplements_col_description"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_numbers_from_zero",
        default=u"0",
        required=False,
    )

    form.widget('enable_editors', SelectFieldWidget)
    enable_editors = schema.Choice(
        title=_(u"title_meeting_config_committees_enable_editors", default=u"Committee editors group enabled?"),
        description=_(
            u"desc_meeting_config_committees_enable_editors",
            default=u"committees_enable_editors_col_description",
        ),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_boolean_vocabulary",
        default=u"0",
        required=False,
    )

    form.widget('enabled', SelectFieldWidget)
    enabled = schema.Choice(
        title=_(u"title_meeting_config_committees_enabled", default=u"Committee enabled?"),
        description=_(u"desc_meeting_config_committees_enabled", default=u"committees_enabled_col_description"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_committees_enabled",
        default=u"1",
        required=False,
    )



class IMeetingConfig(IConfigElement, model.Schema):
    """Dexterity schema for MeetingConfig.

    Step 1 of the Archetypes to Dexterity migration: schema translation only.
    The type registration and content migration are intentionally handled later.
    """

    form.write_permission(folder_title=u"PloneMeeting: Write risky config")
    folder_title = schema.TextLine(
        title=_(u"PloneMeeting_label_folderTitle", default=u"Foldertitle"),
        description=_(u"folder_title_descr", default=u"FolderTitle"),
        required=True,
    )

    form.write_permission(short_name=u"PloneMeeting: Write risky config")
    short_name = schema.TextLine(
        title=_(u"PloneMeeting_label_shortName", default=u"Shortname"),
        description=_(u"short_name_descr", default=u"ShortName"),
        required=True,
    )

    form.write_permission(is_default=u"PloneMeeting: Write risky config")
    is_default = schema.Bool(
        title=_(u"PloneMeeting_label_isDefault", default=u"Isdefault"),
        description=_(u"config_is_default_descr", default=u"IsDefault"),
        defaultFactory=_default_value(u"isDefault"),
        required=False,
    )

    form.write_permission(item_icon_color=u"PloneMeeting: Write risky config")
    form.widget('item_icon_color', SelectFieldWidget)
    item_icon_color = schema.Choice(
        title=_(u"PloneMeeting_label_itemIconColor", default=u"Itemiconcolor"),
        description=_(u"item_icon_color_descr", default=u"ItemIconColor"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_icon_colors",
        defaultFactory=_default_value(u"itemIconColor"),
        required=False,
    )

    form.write_permission(config_group=u"PloneMeeting: Write risky config")
    form.widget('config_group', SelectFieldWidget)
    config_group = schema.Choice(
        title=_(u"PloneMeeting_label_configGroup", default=u"Configgroup"),
        description=_(u"config_group_descr", default=u"ConfigGroup"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_config_groups",
        defaultFactory=_default_value(u"configGroup"),
        required=False,
    )

    form.write_permission(places=u"PloneMeeting: Write risky config")
    form.widget('places', TextAreaFieldWidget)
    places = schema.Text(
        title=_(u"PloneMeeting_label_places", default=u"Places"),
        description=_(u"places_descr", default=u"Places"),
        defaultFactory=_default_value(u"places"),
        required=False,
    )

    form.write_permission(last_meeting_number=u"PloneMeeting: Write harmless config")
    last_meeting_number = schema.Int(
        title=_(u"PloneMeeting_label_lastMeetingNumber", default=u"Lastmeetingnumber"),
        description=_(u"last_meeting_number_descr", default=u"LastMeetingNumber"),
        defaultFactory=_default_value(u"lastMeetingNumber"),
        required=True,
    )

    form.write_permission(yearly_init_meeting_numbers=u"PloneMeeting: Write risky config")
    form.widget('yearly_init_meeting_numbers', CheckBoxFieldWidget)
    yearly_init_meeting_numbers = schema.List(
        title=_(u"PloneMeeting_label_yearlyInitMeetingNumbers", default=u"Yearlyinitmeetingnumbers"),
        description=_(u"yearly_init_meeting_numbers_descr", default=u"YearlyInitMeetingNumbers"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.yearlyinitmeetingnumbersvocabulary",
        ),
        defaultFactory=_default_value(u"yearlyInitMeetingNumbers"),
        required=False,
    )

    form.write_permission(budget_default=u"PloneMeeting: Write risky config")
    budget_default = RichText(
        title=_(u"PloneMeeting_label_budgetDefault", default=u"Budgetdefault"),
        description=_(u"config_budget_default_descr", default=u"BudgetDefault"),
        default_mime_type=u"text/html",
        allowed_mime_types=(u"text/html", ),
        output_mime_type=u"text/x-html-safe",
        defaultFactory=_default_value(u"budgetDefault"),
        required=False,
    )

    form.write_permission(config_version=u"PloneMeeting: Write risky config")
    config_version = schema.TextLine(
        title=_(u"PloneMeeting_label_configVersion", default=u"Configversion"),
        description=_(u"config_version_descr", default=u"ConfigVersion"),
        defaultFactory=_default_value(u"configVersion"),
        required=False,
    )

    form.write_permission(assembly=u"PloneMeeting: Write harmless config")
    form.widget('assembly', TextAreaFieldWidget)
    assembly = schema.Text(
        title=_(u"title_default_assembly", default=u"Assembly"),
        description=_(u"assembly_descr", default=u"Assembly"),
        defaultFactory=_default_value(u"assembly"),
        required=False,
    )

    form.write_permission(assembly_staves=u"PloneMeeting: Write harmless config")
    form.widget('assembly_staves', TextAreaFieldWidget)
    assembly_staves = schema.Text(
        title=_(u"title_default_assembly_staves", default=u"AssemblyStaves"),
        description=_(u"assembly_staves_descr", default=u"AssemblyStaves"),
        defaultFactory=_default_value(u"assemblyStaves"),
        required=False,
    )

    form.write_permission(signatures=u"PloneMeeting: Write harmless config")
    form.widget('signatures', TextAreaFieldWidget)
    signatures = schema.Text(
        title=_(u"title_default_signatures", default=u"Signatures"),
        description=_(u"signatures_descr", default=u"Signatures"),
        defaultFactory=_default_value(u"signatures"),
        required=False,
    )

    form.write_permission(certified_signatures=u"PloneMeeting: Write harmless config")
    form.widget('certified_signatures', DataGridFieldFactory)
    certified_signatures = DataGridField(
        title=_(u"PloneMeeting_label_certifiedSignatures", default=u"Certifiedsignatures"),
        description=_(u"certified_signatures_descr", default=u"CertifiedSignatures"),
        value_type=DictRow(schema=ICertifiedSignaturesRowSchema),
        defaultFactory=_default_value(u"certifiedSignatures"),
        required=False,
    )

    form.write_permission(ordered_contacts=u"PloneMeeting: Write harmless config")
    form.widget('ordered_contacts', OrderedSelectFieldWidget)
    ordered_contacts = schema.List(
        title=_(u"PloneMeeting_label_orderedContacts", default=u"Orderedcontacts"),
        description=_(u"ordered_contacts_descr", default=u"OrderedContacts"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.selectableassemblymembersvocabulary",
        ),
        defaultFactory=_default_value(u"orderedContacts"),
        required=False,
    )

    form.write_permission(ordered_item_initiators=u"PloneMeeting: Write harmless config")
    form.widget('ordered_item_initiators', OrderedSelectFieldWidget)
    ordered_item_initiators = schema.List(
        title=_(u"PloneMeeting_label_orderedItemInitiators", default=u"Orderediteminitiators"),
        description=_(u"ordered_item_initiators_descr", default=u"OrderedItemInitiators"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.selectableiteminitiatorsvocabulary",
        ),
        defaultFactory=_default_value(u"orderedItemInitiators"),
        required=False,
    )

    form.write_permission(selectable_redefined_position_types=u"PloneMeeting: Write harmless config")
    form.widget('selectable_redefined_position_types', CheckBoxFieldWidget)
    selectable_redefined_position_types = schema.List(
        title=_(u"PloneMeeting_label_selectableRedefinedPositionTypes", default=u"Selectableredefinedpositiontypes"),
        description=_(u"selectable_redefined_position_types_descr", default=u"SelectableRedefinedPositionTypes"),
        value_type=schema.Choice(
            vocabulary=u"PMPositionTypes",
        ),
        defaultFactory=_default_value(u"selectableRedefinedPositionTypes"),
        required=False,
    )

    form.write_permission(used_item_attributes=u"PloneMeeting: Write risky config")
    form.widget('used_item_attributes', CheckBoxFieldWidget)
    used_item_attributes = schema.List(
        title=_(u"PloneMeeting_label_usedItemAttributes", default=u"Useditemattributes"),
        description=_(u"used_item_attributes_descr", default=u"UsedItemAttributes"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_used_item_attributes",
        ),
        defaultFactory=_default_value(u"usedItemAttributes"),
        required=False,
    )

    form.write_permission(historized_item_attributes=u"PloneMeeting: Write risky config")
    form.widget('historized_item_attributes', CheckBoxFieldWidget)
    historized_item_attributes = schema.List(
        title=_(u"PloneMeeting_label_historizedItemAttributes", default=u"Historizeditemattributes"),
        description=_(u"historized_item_attrs_descr", default=u"HistorizedItemAttributes"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_attributes",
        ),
        defaultFactory=_default_value(u"historizedItemAttributes"),
        required=False,
    )

    form.write_permission(record_item_history_states=u"PloneMeeting: Write risky config")
    form.widget('record_item_history_states', CheckBoxFieldWidget)
    record_item_history_states = schema.List(
        title=_(u"PloneMeeting_label_recordItemHistoryStates", default=u"Recorditemhistorystates"),
        description=_(u"record_item_history_states_descr", default=u"RecordItemHistoryStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"recordItemHistoryStates"),
        required=False,
    )

    form.write_permission(used_meeting_attributes=u"PloneMeeting: Write risky config")
    form.widget('used_meeting_attributes', CheckBoxFieldWidget)
    used_meeting_attributes = schema.List(
        title=_(u"PloneMeeting_label_usedMeetingAttributes", default=u"Usedmeetingattributes"),
        description=_(u"used_meeting_attributes_descr", default=u"UsedMeetingAttributes"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_used_meeting_attributes",
        ),
        defaultFactory=_default_value(u"usedMeetingAttributes"),
        required=False,
    )

    form.write_permission(ordered_associated_organizations=u"PloneMeeting: Write risky config")
    form.widget('ordered_associated_organizations', OrderedSelectFieldWidget)
    ordered_associated_organizations = schema.List(
        title=_(u"PloneMeeting_label_orderedAssociatedOrganizations", default=u"Orderedassociatedorganizations"),
        description=_(u"ordered_associated_organizations_descr", default=u"OrderedAssociatedOrganizations"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.detailedorganizationsvocabulary",
        ),
        defaultFactory=_default_value(u"orderedAssociatedOrganizations"),
        required=False,
    )

    form.write_permission(ordered_groups_in_charge=u"PloneMeeting: Write risky config")
    form.widget('ordered_groups_in_charge', OrderedSelectFieldWidget)
    ordered_groups_in_charge = schema.List(
        title=_(u"PloneMeeting_label_orderedGroupsInCharge", default=u"Orderedgroupsincharge"),
        description=_(u"ordered_groups_in_charge_descr", default=u"OrderedGroupsInCharge"),
        value_type=schema.Choice(
            vocabulary=u"collective.contact.plonegroup.browser.settings.SortedSelectedOrganizationsElephantVocabulary",
        ),
        defaultFactory=_default_value(u"orderedGroupsInCharge"),
        required=False,
    )

    form.write_permission(include_groups_in_charge_defined_on_proposing_group=u"PloneMeeting: Write risky config")
    include_groups_in_charge_defined_on_proposing_group = schema.Bool(
        title=_(
            u"PloneMeeting_label_includeGroupsInChargeDefinedOnProposingGroup",
            default=u"Includegroupsinchargedefinedonproposinggroup",
        ),
        description=_(
            u"include_groups_in_charge_defined_on_proposing_group_descr",
            default=u"IncludeGroupsInChargeDefinedOnProposingGroup",
        ),
        defaultFactory=_default_value(u"includeGroupsInChargeDefinedOnProposingGroup"),
        required=False,
    )

    form.write_permission(include_groups_in_charge_defined_on_category=u"PloneMeeting: Write risky config")
    include_groups_in_charge_defined_on_category = schema.Bool(
        title=_(
            u"PloneMeeting_label_includeGroupsInChargeDefinedOnCategory",
            default=u"Includegroupsinchargedefinedoncategory",
        ),
        description=_(
            u"include_groups_in_charge_defined_on_category_descr",
            default=u"IncludeGroupsInChargeDefinedOnCategory",
        ),
        defaultFactory=_default_value(u"includeGroupsInChargeDefinedOnCategory"),
        required=False,
    )

    form.write_permission(to_discuss_set_on_item_insert=u"PloneMeeting: Write risky config")
    to_discuss_set_on_item_insert = schema.Bool(
        title=_(u"PloneMeeting_label_toDiscussSetOnItemInsert", default=u"Todiscusssetoniteminsert"),
        description=_(u"to_discuss_set_on_item_insert_descr", default=u"ToDiscussSetOnItemInsert"),
        defaultFactory=_default_value(u"toDiscussSetOnItemInsert"),
        required=False,
    )

    form.write_permission(to_discuss_default=u"PloneMeeting: Write risky config")
    to_discuss_default = schema.Bool(
        title=_(u"PloneMeeting_label_toDiscussDefault", default=u"Todiscussdefault"),
        description=_(u"to_discuss_default_descr", default=u"ToDiscussDefault"),
        defaultFactory=_default_value(u"toDiscussDefault"),
        required=False,
    )

    form.write_permission(to_discuss_late_default=u"PloneMeeting: Write risky config")
    to_discuss_late_default = schema.Bool(
        title=_(u"PloneMeeting_label_toDiscussLateDefault", default=u"Todiscusslatedefault"),
        description=_(u"to_discuss_late_default_descr", default=u"ToDiscussLateDefault"),
        defaultFactory=_default_value(u"toDiscussLateDefault"),
        required=False,
    )

    form.write_permission(item_reference_format=u"PloneMeeting: Write risky config")
    form.widget('item_reference_format', TextAreaFieldWidget)
    item_reference_format = schema.Text(
        title=_(u"PloneMeeting_label_itemReferenceFormat", default=u"Itemreferenceformat"),
        description=_(u"item_reference_format_descr", default=u"ItemReferenceFormat"),
        defaultFactory=_default_value(u"itemReferenceFormat"),
        required=False,
    )

    form.write_permission(compute_item_reference_for_items_out_of_meeting=u"PloneMeeting: Write risky config")
    compute_item_reference_for_items_out_of_meeting = schema.Bool(
        title=_(
            u"PloneMeeting_label_computeItemReferenceForItemsOutOfMeeting",
            default=u"Computeitemreferenceforitemsoutofmeeting",
        ),
        description=_(
            u"compute_item_reference_for_items_out_of_meeting_descr",
            default=u"ComputeItemReferenceForItemsOutOfMeeting",
        ),
        defaultFactory=_default_value(u"computeItemReferenceForItemsOutOfMeeting"),
        required=False,
    )

    form.write_permission(inserting_methods_on_add_item=u"PloneMeeting: Write risky config")
    form.widget('inserting_methods_on_add_item', DataGridFieldFactory)
    inserting_methods_on_add_item = DataGridField(
        title=_(u"PloneMeeting_label_insertingMethodsOnAddItem", default=u"Insertingmethodsonadditem"),
        description=_(u"inserting_methods_on_add_item_descr", default=u"insertingMethodsOnAddItem"),
        value_type=DictRow(schema=IInsertingMethodsOnAddItemRowSchema),
        defaultFactory=_default_value(u"insertingMethodsOnAddItem"),
        required=True,
    )

    form.write_permission(selectable_privacies=u"PloneMeeting: Write risky config")
    form.widget('selectable_privacies', OrderedSelectFieldWidget)
    selectable_privacies = schema.List(
        title=_(u"PloneMeeting_label_selectablePrivacies", default=u"selectableprivacies"),
        description=_(u"selectable_privacies_descr", default=u"SelectablePrivacies"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.selectableprivaciesvocabulary",
        ),
        defaultFactory=_default_value(u"selectablePrivacies"),
        required=False,
    )

    form.write_permission(all_item_tags=u"PloneMeeting: Write risky config")
    form.widget('all_item_tags', TextAreaFieldWidget)
    all_item_tags = schema.Text(
        title=_(u"PloneMeeting_label_allItemTags", default=u"Allitemtags"),
        description=_(u"all_item_tags_descr", default=u"AllItemTags"),
        defaultFactory=_default_value(u"allItemTags"),
        required=False,
    )

    form.write_permission(sort_all_item_tags=u"PloneMeeting: Write risky config")
    sort_all_item_tags = schema.Bool(
        title=_(u"PloneMeeting_label_sortAllItemTags", default=u"Sortallitemtags"),
        description=_(u"sort_all_item_tags_descr", default=u"SortAllItemTags"),
        defaultFactory=_default_value(u"sortAllItemTags"),
        required=False,
    )

    form.write_permission(item_fields_to_keep_config_sorting_for=u"PloneMeeting: Write risky config")
    form.widget('item_fields_to_keep_config_sorting_for', CheckBoxFieldWidget)
    item_fields_to_keep_config_sorting_for = schema.List(
        title=_(u"PloneMeeting_label_itemFieldsToKeepConfigSortingFor", default=u"Itemfieldstokeepconfigsortingfor"),
        description=_(u"item_fields_to_keep_config_sorting_for_descr", default=u"ItemFieldsToKeepConfigSortingFor"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_fields_to_keep_config_sorting_for",
        ),
        defaultFactory=_default_value(u"itemFieldsToKeepConfigSortingFor"),
        required=False,
    )

    form.write_permission(list_types=u"PloneMeeting: Write risky config")
    form.widget('list_types', DataGridFieldFactory)
    list_types = DataGridField(
        title=_(u"PloneMeeting_label_listTypes", default=u"Listtypes"),
        description=_(u"list_types_descr", default=u"ListTypes"),
        value_type=DictRow(schema=IListTypesRowSchema),
        defaultFactory=_default_value(u"listTypes"),
        required=False,
    )

    form.write_permission(xhtml_transform_fields=u"PloneMeeting: Write risky config")
    form.widget('xhtml_transform_fields', CheckBoxFieldWidget)
    xhtml_transform_fields = schema.List(
        title=_(u"PloneMeeting_label_xhtmlTransformFields", default=u"Xhtmltransformfields"),
        description=_(u"xhtml_transform_fields_descr", default=u"XhtmlTransformFields"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_all_rich_text_fields",
        ),
        defaultFactory=_default_value(u"xhtmlTransformFields"),
        required=False,
    )

    form.write_permission(xhtml_transform_types=u"PloneMeeting: Write risky config")
    form.widget('xhtml_transform_types', CheckBoxFieldWidget)
    xhtml_transform_types = schema.List(
        title=_(u"PloneMeeting_label_xhtmlTransformTypes", default=u"Xhtmltransformtypes"),
        description=_(u"xhtml_transform_types_descr", default=u"XhtmlTransformTypes"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_transform_types",
        ),
        defaultFactory=_default_value(u"xhtmlTransformTypes"),
        required=False,
    )

    form.write_permission(validation_deadline_default=u"PloneMeeting: Write risky config")
    validation_deadline_default = schema.TextLine(
        title=_(u"PloneMeeting_label_validationDeadlineDefault", default=u"Validationdeadlinedefault"),
        description=_(u"validation_deadline_default_descr", default=u"ValidationDeadlineDefault"),
        defaultFactory=_default_value(u"validationDeadlineDefault"),
        required=False,
    )

    form.write_permission(freeze_deadline_default=u"PloneMeeting: Write risky config")
    freeze_deadline_default = schema.TextLine(
        title=_(u"PloneMeeting_label_freezeDeadlineDefault", default=u"Freezedeadlinedefault"),
        description=_(u"freeze_deadline_default_descr", default=u"FreezeDeadlineDefault"),
        defaultFactory=_default_value(u"freezeDeadlineDefault"),
        required=False,
    )

    form.write_permission(meeting_configs_to_clone_to=u"PloneMeeting: Write risky config")
    form.widget('meeting_configs_to_clone_to', DataGridFieldFactory)
    meeting_configs_to_clone_to = DataGridField(
        title=_(u"PloneMeeting_label_meetingConfigsToCloneTo", default=u"Meetingconfigstocloneto"),
        description=_(u"meeting_configs_to_clone_to_descr", default=u"MeetingConfigsToCloneTo"),
        value_type=DictRow(schema=IMeetingConfigsToCloneToRowSchema),
        defaultFactory=_default_value(u"meetingConfigsToCloneTo"),
        required=False,
    )

    form.write_permission(item_auto_sent_to_other_mc_states=u"PloneMeeting: Write risky config")
    form.widget('item_auto_sent_to_other_mc_states', CheckBoxFieldWidget)
    item_auto_sent_to_other_mc_states = schema.List(
        title=_(u"PloneMeeting_label_itemAutoSentToOtherMCStates", default=u"Itemautosenttoothermcstates"),
        description=_(u"item_auto_sent_to_other_mc_states_descr", default=u"ItemAutoSentToOtherMCStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_auto_sent_to_other_mc_states",
        ),
        defaultFactory=_default_value(u"itemAutoSentToOtherMCStates"),
        required=False,
    )

    form.write_permission(item_manual_sent_to_other_mc_states=u"PloneMeeting: Write risky config")
    form.widget('item_manual_sent_to_other_mc_states', CheckBoxFieldWidget)
    item_manual_sent_to_other_mc_states = schema.List(
        title=_(u"PloneMeeting_label_itemManualSentToOtherMCStates", default=u"Itemmanualsenttoothermcstates"),
        description=_(u"item_manual_sent_to_other_mc_states_descr", default=u"ItemManualSentToOtherMCStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemManualSentToOtherMCStates"),
        required=False,
    )

    form.write_permission(contents_kept_on_sent_to_other_mc=u"PloneMeeting: Write risky config")
    form.widget('contents_kept_on_sent_to_other_mc', CheckBoxFieldWidget)
    contents_kept_on_sent_to_other_mc = schema.List(
        title=_(u"PloneMeeting_label_contentsKeptOnSentToOtherMC", default=u"Contentskeptonsenttoothermc"),
        description=_(u"contents_kept_on_sent_to_other_mc_descr", default=u"ContentsKeptOnSentToOtherMC"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_contents_kept_on_sent_to_other_mcs",
        ),
        defaultFactory=_default_value(u"contentsKeptOnSentToOtherMC"),
        required=False,
    )

    form.write_permission(advices_kept_on_sent_to_other_mc=u"PloneMeeting: Write risky config")
    form.widget('advices_kept_on_sent_to_other_mc', CheckBoxFieldWidget)
    advices_kept_on_sent_to_other_mc = schema.List(
        title=_(u"PloneMeeting_label_advicesKeptOnSentToOtherMC", default=u"AdviceskeptonSenttoothermc"),
        description=_(u"advices_kept_on_sent_to_other_mc_descr", default=u"AdvicesKeptOnSentToOtherMC"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.askedadvicesvocabulary",
        ),
        defaultFactory=_default_value(u"advicesKeptOnSentToOtherMC"),
        required=False,
    )

    form.write_permission(enabled_item_actions=u"PloneMeeting: Write risky config")
    form.widget('enabled_item_actions', CheckBoxFieldWidget)
    enabled_item_actions = schema.List(
        title=_(u"PloneMeeting_label_enabledItemActions", default=u"enableditemactions"),
        value_type=schema.Choice(
            vocabulary=u"EnabledItemActions",
        ),
        defaultFactory=_default_value(u"enabledItemActions"),
        required=False,
    )

    form.write_permission(annex_to_print_mode=u"PloneMeeting: Write risky config")
    form.widget('annex_to_print_mode', SelectFieldWidget)
    annex_to_print_mode = schema.Choice(
        title=_(u"PloneMeeting_label_annexToPrintMode", default=u"Annextoprintmode"),
        description=_(u"annex_to_print_mode_descr", default=u"AnnexToPrintMode"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_annex_to_print_modes",
        defaultFactory=_default_value(u"annexToPrintMode"),
        required=False,
    )

    form.write_permission(keep_original_to_print_of_cloned_items=u"PloneMeeting: Write risky config")
    keep_original_to_print_of_cloned_items = schema.Bool(
        title=_(u"PloneMeeting_label_keepOriginalToPrintOfClonedItems", default=u"Keeporiginaltoprintofcloneditems"),
        description=_(u"keep_original_to_print_of_cloned_items_descr", default=u"KeepOriginalToPrintOfClonedItems"),
        defaultFactory=_default_value(u"keepOriginalToPrintOfClonedItems"),
        required=False,
    )

    form.write_permission(remove_annexes_previews_on_meeting_closure=u"PloneMeeting: Write risky config")
    remove_annexes_previews_on_meeting_closure = schema.Bool(
        title=_(
            u"PloneMeeting_label_removeAnnexesPreviewsOnMeetingClosure",
            default=u"Removeannexespreviewsonmeetingclosure",
        ),
        description=_(
            u"remove_annexes_previews_on_meeting_closure_descr",
            default=u"RemoveAnnexesPreviewsOnMeetingClosure",
        ),
        defaultFactory=_default_value(u"removeAnnexesPreviewsOnMeetingClosure"),
        required=False,
    )

    form.write_permission(css_transforms=u"PloneMeeting: Write risky config")
    form.widget('css_transforms', DataGridFieldFactory)
    css_transforms = DataGridField(
        title=_(u"PloneMeeting_label_cssTransforms", default=u"Csstransforms"),
        description=_(u"css_transforms_descr", default=u"CssTransforms"),
        value_type=DictRow(schema=ICssTransformsRowSchema),
        defaultFactory=_default_value(u"cssTransforms"),
        required=False,
    )

    form.write_permission(item_workflow=u"PloneMeeting: Write risky config")
    form.widget('item_workflow', SelectFieldWidget)
    item_workflow = schema.Choice(
        title=_(u"PloneMeeting_label_itemWorkflow", default=u"Itemworkflow"),
        description=_(u"item_workflow_descr", default=u"ItemWorkflow"),
        vocabulary=u"ItemWorkflows",
        defaultFactory=_default_value(u"itemWorkflow"),
        required=True,
    )

    form.write_permission(item_conditions_interface=u"PloneMeeting: Write risky config")
    item_conditions_interface = schema.TextLine(
        title=_(u"PloneMeeting_label_itemConditionsInterface", default=u"Itemconditionsinterface"),
        description=_(u"item_conditions_interface_descr", default=u"ItemConditionsInterface"),
        defaultFactory=_default_value(u"itemConditionsInterface"),
        required=False,
    )

    form.write_permission(item_actions_interface=u"PloneMeeting: Write risky config")
    item_actions_interface = schema.TextLine(
        title=_(u"PloneMeeting_label_itemActionsInterface", default=u"Itemactionsinterface"),
        description=_(u"item_actions_interface_descr", default=u"ItemActionsInterface"),
        defaultFactory=_default_value(u"itemActionsInterface"),
        required=False,
    )

    form.write_permission(meeting_workflow=u"PloneMeeting: Write risky config")
    form.widget('meeting_workflow', SelectFieldWidget)
    meeting_workflow = schema.Choice(
        title=_(u"PloneMeeting_label_meetingWorkflow", default=u"Meetingworkflow"),
        description=_(u"meeting_workflow_descr", default=u"MeetingWorkflow"),
        vocabulary=u"MeetingWorkflows",
        defaultFactory=_default_value(u"meetingWorkflow"),
        required=True,
    )

    form.write_permission(meeting_conditions_interface=u"PloneMeeting: Write risky config")
    meeting_conditions_interface = schema.TextLine(
        title=_(u"PloneMeeting_label_meetingConditionsInterface", default=u"Meetingconditionsinterface"),
        description=_(u"meeting_conditions_interface_descr", default=u"MeetingConditionsInterface"),
        defaultFactory=_default_value(u"meetingConditionsInterface"),
        required=False,
    )

    form.write_permission(meeting_actions_interface=u"PloneMeeting: Write risky config")
    meeting_actions_interface = schema.TextLine(
        title=_(u"PloneMeeting_label_meetingActionsInterface", default=u"Meetingactionsinterface"),
        description=_(u"meeting_actions_interface_descr", default=u"MeetingActionsInterface"),
        defaultFactory=_default_value(u"meetingActionsInterface"),
        required=False,
    )

    form.write_permission(workflow_adaptations=u"PloneMeeting: Write risky config")
    form.widget('workflow_adaptations', CheckBoxFieldWidget)
    workflow_adaptations = schema.List(
        title=_(u"PloneMeeting_label_workflowAdaptations", default=u"Workflowadaptations"),
        description=_(u"workflow_adaptations_descr", default=u"WorkflowAdaptations"),
        value_type=schema.Choice(
            vocabulary=u"WorkflowAdaptations",
        ),
        defaultFactory=_default_value(u"workflowAdaptations"),
        required=False,
    )

    form.write_permission(item_wf_validation_levels=u"PloneMeeting: Write risky config")
    form.widget('item_wf_validation_levels', DataGridFieldFactory)
    item_wf_validation_levels = DataGridField(
        title=_(u"PloneMeeting_label_itemWFValidationLevels", default=u"Itemwfvalidationlevels"),
        description=_(u"item_wf_validation_levels_descr", default=u"ItemWFValidationLevels"),
        value_type=DictRow(schema=IItemWfValidationLevelsRowSchema),
        defaultFactory=_default_value(u"itemWFValidationLevels"),
        required=False,
    )

    form.write_permission(transitions_to_confirm=u"PloneMeeting: Write risky config")
    form.widget('transitions_to_confirm', CheckBoxFieldWidget)
    transitions_to_confirm = schema.List(
        title=_(u"PloneMeeting_label_transitionsToConfirm", default=u"Transitionstoconfirm"),
        description=_(u"transitions_to_confirm_descr", default=u"TransitionsToConfirm"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_all_transitions",
        ),
        defaultFactory=_default_value(u"transitionsToConfirm"),
        required=False,
    )

    form.write_permission(on_transition_field_transforms=u"PloneMeeting: Write risky config")
    form.widget('on_transition_field_transforms', DataGridFieldFactory)
    on_transition_field_transforms = DataGridField(
        title=_(u"PloneMeeting_label_onTransitionFieldTransforms", default=u"Ontransitionfieldtransforms"),
        description=_(u"on_transition_field_transforms_descr", default=u"OnTransitionFieldTransforms"),
        value_type=DictRow(schema=IOnTransitionFieldTransformsRowSchema),
        defaultFactory=_default_value(u"onTransitionFieldTransforms"),
        required=False,
    )

    form.write_permission(on_meeting_transition_item_action_to_execute=u"PloneMeeting: Write risky config")
    form.widget('on_meeting_transition_item_action_to_execute', DataGridFieldFactory)
    on_meeting_transition_item_action_to_execute = DataGridField(
        title=_(
            u"PloneMeeting_label_onMeetingTransitionItemActionToExecute",
            default=u"Onmeetingtransitionitemactiontoexecute",
        ),
        description=_(
            u"on_meeting_transition_item_action_to_execute_descr",
            default=u"OnMeetingTransitionItemActionToExecute",
        ),
        value_type=DictRow(schema=IOnMeetingTransitionItemActionToExecuteRowSchema),
        defaultFactory=_default_value(u"onMeetingTransitionItemActionToExecute"),
        required=False,
    )

    form.write_permission(meeting_present_item_when_no_current_meeting_states=u"PloneMeeting: Write risky config")
    form.widget('meeting_present_item_when_no_current_meeting_states', CheckBoxFieldWidget)
    meeting_present_item_when_no_current_meeting_states = schema.List(
        title=_(
            u"PloneMeeting_label_meetingPresentItemWhenNoCurrentMeetingStates",
            default=u"Meetingpresentitemwhennocurrentmeetingstates",
        ),
        description=_(
            u"meeting_present_item_when_no_current_meeting_states_descr",
            default=u"MeetingPresentItemWhenNoCurrentMeetingStates",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_states",
        ),
        defaultFactory=_default_value(u"meetingPresentItemWhenNoCurrentMeetingStates"),
        required=False,
    )

    form.write_permission(item_preferred_meeting_states=u"PloneMeeting: Write risky config")
    form.widget('item_preferred_meeting_states', CheckBoxFieldWidget)
    item_preferred_meeting_states = schema.List(
        title=_(u"PloneMeeting_label_itemPreferredMeetingStates", default=u"itemPreferredMeetingStates"),
        description=_(u"itemPreferredMeetingStates_descr", default=u"itemPreferredMeetingStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_states",
        ),
        defaultFactory=_default_value(u"itemPreferredMeetingStates"),
        required=False,
    )

    form.write_permission(item_columns=u"PloneMeeting: Write risky config")
    form.widget('item_columns', CheckBoxFieldWidget)
    item_columns = schema.List(
        title=_(u"PloneMeeting_label_itemColumns", default=u"Itemcolumns"),
        description=_(u"item_columns_descr", default=u"ItemColumns"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_columns",
        ),
        defaultFactory=_default_value(u"itemColumns"),
        required=False,
    )

    form.write_permission(available_items_list_visible_columns=u"PloneMeeting: Write risky config")
    form.widget('available_items_list_visible_columns', CheckBoxFieldWidget)
    available_items_list_visible_columns = schema.List(
        title=_(u"PloneMeeting_label_availableItemsListVisibleColumns", default=u"AvailableItemslistvisiblecolumns"),
        description=_(u"available_items_list_visible_columns_descr", default=u"availableItemsListVisibleColumns"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_available_items_list_visible_columns",
        ),
        defaultFactory=_default_value(u"availableItemsListVisibleColumns"),
        required=False,
    )

    form.write_permission(items_list_visible_columns=u"PloneMeeting: Write risky config")
    form.widget('items_list_visible_columns', CheckBoxFieldWidget)
    items_list_visible_columns = schema.List(
        title=_(u"PloneMeeting_label_itemsListVisibleColumns", default=u"Itemslistvisiblecolumns"),
        description=_(u"items_list_visible_columns_descr", default=u"ItemsListVisibleColumns"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_items_list_visible_columns",
        ),
        defaultFactory=_default_value(u"itemsListVisibleColumns"),
        required=False,
    )

    form.write_permission(item_actions_column_config=u"PloneMeeting: Write risky config")
    form.widget('item_actions_column_config', CheckBoxFieldWidget)
    item_actions_column_config = schema.List(
        title=_(u"PloneMeeting_label_itemActionsColumnConfig", default=u"Itemactionscolumnconfig"),
        description=_(u"item_actions_column_config_descr", default=u"ItemActionsColumnConfig"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_actions_column_config",
        ),
        defaultFactory=_default_value(u"itemActionsColumnConfig"),
        required=False,
    )

    form.write_permission(meeting_columns=u"PloneMeeting: Write risky config")
    form.widget('meeting_columns', CheckBoxFieldWidget)
    meeting_columns = schema.List(
        title=_(u"PloneMeeting_label_meetingColumns", default=u"Meetingcolumns"),
        description=_(u"meeting_columns_descr", default=u"MeetingColumns"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_columns",
        ),
        defaultFactory=_default_value(u"meetingColumns"),
        required=False,
    )

    form.write_permission(enabled_annexes_batch_actions=u"PloneMeeting: Write risky config")
    form.widget('enabled_annexes_batch_actions', CheckBoxFieldWidget)
    enabled_annexes_batch_actions = schema.List(
        title=_(u"PloneMeeting_label_enabledAnnexesBatchActions", default=u"enabledannexesbatchactions"),
        description=_(u"enabled_annexes_batch_actions_descr", default=u"EnabledAnnexesBatchActions"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_annexes_batch_actions",
        ),
        defaultFactory=_default_value(u"enabledAnnexesBatchActions"),
        required=False,
    )

    form.write_permission(display_available_items_to=u"PloneMeeting: Write risky config")
    form.widget('display_available_items_to', CheckBoxFieldWidget)
    display_available_items_to = schema.List(
        title=_(u"PloneMeeting_label_displayAvailableItemsTo", default=u"Displayavailableitemsto"),
        description=_(u"display_available_items_to_descr", default=u"DisplayAvailableItemsTo"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_display_available_items_to",
        ),
        defaultFactory=_default_value(u"displayAvailableItemsTo"),
        required=False,
    )

    form.write_permission(redirect_to_next_meeting=u"PloneMeeting: Write risky config")
    form.widget('redirect_to_next_meeting', CheckBoxFieldWidget)
    redirect_to_next_meeting = schema.List(
        title=_(u"PloneMeeting_label_redirectToNextMeeting", default=u"Redirecttonextmeeting"),
        description=_(u"redirect_to_next_meeting_descr", default=u"RedirectToNextMeeting"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_redirect_to_next_meeting",
        ),
        defaultFactory=_default_value(u"redirectToNextMeeting"),
        required=False,
    )

    form.write_permission(items_visible_fields=u"PloneMeeting: Write risky config")
    form.widget('items_visible_fields', OrderedSelectFieldWidget)
    items_visible_fields = schema.List(
        title=_(u"PloneMeeting_label_itemsVisibleFields", default=u"Itemsvisiblefields"),
        description=_(u"items_visible_fields_descr", default=u"ItemsVisibleFields"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_items_visible_fields",
        ),
        defaultFactory=_default_value(u"itemsVisibleFields"),
        required=False,
    )

    form.write_permission(items_not_viewable_visible_fields=u"PloneMeeting: Write risky config")
    form.widget('items_not_viewable_visible_fields', OrderedSelectFieldWidget)
    items_not_viewable_visible_fields = schema.List(
        title=_(u"PloneMeeting_label_itemsNotViewableVisibleFields", default=u"Itemsnotviewablevisiblefields"),
        description=_(u"items_not_viewable_visible_fields_descr", default=u"ItemsNotViewableVisibleFields"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_items_not_viewable_visible_fields",
        ),
        defaultFactory=_default_value(u"itemsNotViewableVisibleFields"),
        required=False,
    )

    form.write_permission(items_not_viewable_visible_fields_tal_expr=u"PloneMeeting: Write risky config")
    form.widget('items_not_viewable_visible_fields_tal_expr', TextAreaFieldWidget)
    items_not_viewable_visible_fields_tal_expr = schema.Text(
        title=_(
            u"PloneMeeting_label_itemsNotViewableVisibleFieldsTALExpr",
            default=u"Itemsnotviewablevisiblefieldstalexpr",
        ),
        description=_(
            u"items_not_viewable_visible_fields_tal_expr_descr",
            default=u"ItemsNotViewableVisibleFieldsTALExpr",
        ),
        defaultFactory=_default_value(u"itemsNotViewableVisibleFieldsTALExpr"),
        required=False,
    )

    form.write_permission(items_list_visible_fields=u"PloneMeeting: Write risky config")
    form.widget('items_list_visible_fields', OrderedSelectFieldWidget)
    items_list_visible_fields = schema.List(
        title=_(u"PloneMeeting_label_itemsListVisibleFields", default=u"Itemslistvisiblefields"),
        description=_(u"items_list_visible_fields_descr", default=u"ItemsListVisibleFields"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_items_list_visible_fields",
        ),
        defaultFactory=_default_value(u"itemsListVisibleFields"),
        required=False,
    )

    form.write_permission(max_shown_meetings=u"PloneMeeting: Write risky config")
    max_shown_meetings = schema.Int(
        title=_(u"PloneMeeting_label_maxShownMeetings", default=u"Maxshownmeetings"),
        description=_(u"max_shown_meetings_descr", default=u"MaxShownMeetings"),
        defaultFactory=_default_value(u"maxShownMeetings"),
        required=True,
    )

    form.write_permission(to_do_list_searches=u"PloneMeeting: Write risky config")
    form.widget('to_do_list_searches', OrderedSelectFieldWidget)
    to_do_list_searches = schema.List(
        title=_(u"PloneMeeting_label_toDoListSearches", default=u"Todolistsearches"),
        description=_(u"to_do_list_searches", default=u"ToDoListSearches"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_to_do_list_searches",
        ),
        defaultFactory=_default_value(u"toDoListSearches"),
        required=False,
    )

    form.write_permission(dashboard_items_listings_filters=u"PloneMeeting: Write risky config")
    form.widget('dashboard_items_listings_filters', CheckBoxFieldWidget)
    dashboard_items_listings_filters = schema.List(
        title=_(u"PloneMeeting_label_dashboardItemsListingsFilters", default=u"Dashboarditemslistingsfilters"),
        description=_(u"dashboard_items_listings_filters_descr", default=u"DashboardItemsListingsFilters"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_dashboard_items_listings_filters",
        ),
        defaultFactory=_default_value(u"dashboardItemsListingsFilters"),
        required=False,
    )

    form.write_permission(dashboard_meeting_available_items_filters=u"PloneMeeting: Write risky config")
    form.widget('dashboard_meeting_available_items_filters', CheckBoxFieldWidget)
    dashboard_meeting_available_items_filters = schema.List(
        title=_(
            u"PloneMeeting_label_dashboardMeetingAvailableItemsFilters",
            default=u"Dashboardmeetingavailableitemsfilters",
        ),
        description=_(
            u"dashboard_meeting_available_items_filters_descr",
            default=u"DashboardMeetingAvailableItemsFilters",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_dashboard_items_listings_filters",
        ),
        defaultFactory=_default_value(u"dashboardMeetingAvailableItemsFilters"),
        required=False,
    )

    form.write_permission(dashboard_meeting_linked_items_filters=u"PloneMeeting: Write risky config")
    form.widget('dashboard_meeting_linked_items_filters', CheckBoxFieldWidget)
    dashboard_meeting_linked_items_filters = schema.List(
        title=_(
            u"PloneMeeting_label_dashboardMeetingLinkedItemsFilters",
            default=u"Dashboardmeetinglinkeditemsfilters",
        ),
        description=_(u"dashboard_meeting_linked_items_filters_descr", default=u"DashboardMeetingLinkedItemsFilters"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_dashboard_items_listings_filters",
        ),
        defaultFactory=_default_value(u"dashboardMeetingLinkedItemsFilters"),
        required=False,
    )

    form.write_permission(dashboard_meetings_listings_filters=u"PloneMeeting: Write risky config")
    form.widget('dashboard_meetings_listings_filters', CheckBoxFieldWidget)
    dashboard_meetings_listings_filters = schema.List(
        title=_(u"PloneMeeting_label_dashboardMeetingsListingsFilters", default=u"Dashboardmeetingslistingsfilters"),
        description=_(u"dashboard_meetings_listings_filters_descr", default=u"DashboardMeetingsListingsFilters"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_dashboard_meetings_listings_filters",
        ),
        defaultFactory=_default_value(u"dashboardMeetingsListingsFilters"),
        required=False,
    )

    form.write_permission(groups_hidden_in_dashboard_filter=u"PloneMeeting: Write risky config")
    form.widget('groups_hidden_in_dashboard_filter', CheckBoxFieldWidget)
    groups_hidden_in_dashboard_filter = schema.List(
        title=_(u"PloneMeeting_label_groupsHiddenInDashboardFilter", default=u"Groupshiddenindashboardfilter"),
        description=_(u"groups_hidden_in_dashboard_filter_descr", default=u"GroupsHiddenInDashboardFilter"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.proposinggroupsvocabulary",
        ),
        defaultFactory=_default_value(u"groupsHiddenInDashboardFilter"),
        required=False,
    )

    form.write_permission(users_hidden_in_dashboard_filter=u"PloneMeeting: Write risky config")
    form.widget('users_hidden_in_dashboard_filter', CheckBoxFieldWidget)
    users_hidden_in_dashboard_filter = schema.List(
        title=_(u"PloneMeeting_label_usersHiddenInDashboardFilter", default=u"Usershiddenindashboardfilter"),
        description=_(u"users_hidden_in_dashboard_filter_descr", default=u"UsersHiddenInDashboardFilter"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.creatorsvocabulary",
        ),
        defaultFactory=_default_value(u"usersHiddenInDashboardFilter"),
        required=False,
    )

    form.write_permission(max_shown_listings=u"PloneMeeting: Write risky config")
    form.widget('max_shown_listings', SelectFieldWidget)
    max_shown_listings = schema.Choice(
        title=_(u"PloneMeeting_label_maxShownListings", default=u"Maxshownlistings"),
        description=_(u"max_shown_listings_descr", default=u"MaxShownListings"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_results_per_page",
        defaultFactory=_default_value(u"maxShownListings"),
        required=False,
    )

    form.write_permission(max_shown_available_items=u"PloneMeeting: Write risky config")
    form.widget('max_shown_available_items', SelectFieldWidget)
    max_shown_available_items = schema.Choice(
        title=_(u"PloneMeeting_label_maxShownAvailableItems", default=u"Maxshownavailableitems"),
        description=_(u"max_shown_available_items_descr", default=u"MaxShownAvailableItems"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_results_per_page",
        defaultFactory=_default_value(u"maxShownAvailableItems"),
        required=False,
    )

    form.write_permission(max_shown_meeting_items=u"PloneMeeting: Write risky config")
    form.widget('max_shown_meeting_items', SelectFieldWidget)
    max_shown_meeting_items = schema.Choice(
        title=_(u"PloneMeeting_label_maxShownMeetingItems", default=u"Maxshownmeetingitems"),
        description=_(u"max_shown_meeting_items_descr", default=u"MaxShownMeetingItems"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_results_per_page",
        defaultFactory=_default_value(u"maxShownMeetingItems"),
        required=False,
    )

    form.write_permission(mail_mode=u"PloneMeeting: Write risky config")
    form.widget('mail_mode', SelectFieldWidget)
    mail_mode = schema.Choice(
        title=_(u"PloneMeeting_label_mailMode", default=u"Mailmode"),
        description=_(u"mail_mode_descr", default=u"MailMode"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_mail_modes",
        defaultFactory=_default_value(u"mailMode"),
        required=False,
    )

    form.write_permission(mail_item_events=u"PloneMeeting: Write risky config")
    form.widget('mail_item_events', CheckBoxFieldWidget)
    mail_item_events = schema.List(
        title=_(u"PloneMeeting_label_mailItemEvents", default=u"Mailitemevents"),
        description=_(u"mail_item_events_descr", default=u"MailItemEvents"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_events",
        ),
        defaultFactory=_default_value(u"mailItemEvents"),
        required=False,
    )

    form.write_permission(mail_meeting_events=u"PloneMeeting: Write risky config")
    form.widget('mail_meeting_events', CheckBoxFieldWidget)
    mail_meeting_events = schema.List(
        title=_(u"PloneMeeting_label_mailMeetingEvents", default=u"Mailmeetingevents"),
        description=_(u"mail_meeting_events", default=u"MailMeetingEvents"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_events",
        ),
        defaultFactory=_default_value(u"mailMeetingEvents"),
        required=False,
    )

    form.write_permission(use_advices=u"PloneMeeting: Write risky config")
    use_advices = schema.Bool(
        title=_(u"PloneMeeting_label_useAdvices", default=u"Useadvices"),
        description=_(u"use_advices_descr", default=u"UseAdvices"),
        defaultFactory=_default_value(u"useAdvices"),
        required=False,
    )

    form.write_permission(used_advice_types=u"PloneMeeting: Write risky config")
    form.widget('used_advice_types', CheckBoxFieldWidget)
    used_advice_types = schema.List(
        title=_(u"PloneMeeting_label_usedAdviceTypes", default=u"Usedadvicetypes"),
        description=_(u"used_advice_types_descr", default=u"UsedAdviceTypes"),
        value_type=schema.Choice(
            vocabulary=u"ConfigAdviceTypes",
        ),
        defaultFactory=_default_value(u"usedAdviceTypes"),
        required=False,
    )

    form.write_permission(default_advice_type=u"PloneMeeting: Write risky config")
    form.widget('default_advice_type', SelectFieldWidget)
    default_advice_type = schema.Choice(
        title=_(u"PloneMeeting_label_defaultAdviceType", default=u"Defaultadvicetype"),
        description=_(u"default_advice_type_descr", default=u"DefaultAdviceType"),
        vocabulary=u"ConfigAdviceTypes",
        defaultFactory=_default_value(u"defaultAdviceType"),
        required=False,
    )

    form.write_permission(selectable_advisers=u"PloneMeeting: Write risky config")
    form.widget('selectable_advisers', CheckBoxFieldWidget)
    selectable_advisers = schema.List(
        title=_(u"PloneMeeting_label_selectableAdvisers", default=u"Selectableadvisers"),
        description=_(u"selectable_advisers_descr", default=u"SelectableAdvisers"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_advisers",
        ),
        defaultFactory=_default_value(u"selectableAdvisers"),
        required=False,
    )

    form.write_permission(selectable_adviser_users=u"PloneMeeting: Write risky config")
    form.widget('selectable_adviser_users', CheckBoxFieldWidget)
    selectable_adviser_users = schema.List(
        title=_(u"PloneMeeting_label_selectableAdviserUsers", default=u"Selectableadviserusers"),
        description=_(u"selectable_adviser_users_descr", default=u"SelectableAdviserUsers"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_advisers",
        ),
        defaultFactory=_default_value(u"selectableAdvisers"),
        required=False,
    )

    form.write_permission(item_advice_states=u"PloneMeeting: Write risky config")
    form.widget('item_advice_states', CheckBoxFieldWidget)
    item_advice_states = schema.List(
        title=_(u"PloneMeeting_label_itemAdviceStates", default=u"Itemadvicestates"),
        description=_(u"item_advice_states_descr", default=u"ItemAdviceStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemAdviceStates"),
        required=False,
    )

    form.write_permission(item_advice_edit_states=u"PloneMeeting: Write risky config")
    form.widget('item_advice_edit_states', CheckBoxFieldWidget)
    item_advice_edit_states = schema.List(
        title=_(u"PloneMeeting_label_itemAdviceEditStates", default=u"Itemadviceeditstates"),
        description=_(u"item_advice_edit_states_descr", default=u"ItemAdviceEditStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemAdviceEditStates"),
        required=False,
    )

    form.write_permission(item_advice_view_states=u"PloneMeeting: Write risky config")
    form.widget('item_advice_view_states', CheckBoxFieldWidget)
    item_advice_view_states = schema.List(
        title=_(u"PloneMeeting_label_itemAdviceViewStates", default=u"Itemadviceviewstates"),
        description=_(u"item_advice_view_states_descr", default=u"ItemAdviceViewStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemAdviceViewStates"),
        required=False,
    )

    form.write_permission(keep_access_to_item_when_advice=u"PloneMeeting: Write risky config")
    form.widget('keep_access_to_item_when_advice', SelectFieldWidget)
    keep_access_to_item_when_advice = schema.Choice(
        title=_(u"PloneMeeting_label_keepAccessToItemWhenAdvice", default=u"Keepaccesstoitemwhenadvice"),
        description=_(u"keep_access_to_item_when_advice_descr", default=u"KeepAccessToItemWhenAdvice"),
        vocabulary=u"Products.PloneMeeting.vocabularies.keep_access_to_item_when_advice_vocabulary",
        defaultFactory=_default_value(u"keepAccessToItemWhenAdvice"),
        required=False,
    )

    form.write_permission(enable_advice_invalidation=u"PloneMeeting: Write risky config")
    enable_advice_invalidation = schema.Bool(
        title=_(u"PloneMeeting_label_enableAdviceInvalidation", default=u"Enableadviceinvalidation"),
        description=_(u"enable_advice_invalidation_descr", default=u"EnableAdviceInvalidation"),
        defaultFactory=_default_value(u"enableAdviceInvalidation"),
        required=False,
    )

    form.write_permission(item_advice_invalidate_states=u"PloneMeeting: Write risky config")
    form.widget('item_advice_invalidate_states', CheckBoxFieldWidget)
    item_advice_invalidate_states = schema.List(
        title=_(u"PloneMeeting_label_itemAdviceInvalidateStates", default=u"Itemadviceinvalidatestates"),
        description=_(u"item_advice_invalidate_states", default=u"ItemAdviceInvalidateStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemAdviceInvalidateStates"),
        required=False,
    )

    form.write_permission(advice_style=u"PloneMeeting: Write risky config")
    form.widget('advice_style', SelectFieldWidget)
    advice_style = schema.Choice(
        title=_(u"PloneMeeting_label_adviceStyle", default=u"Advicestyle"),
        description=_(u"advice_style_descr", default=u"AdviceStyle"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_advice_styles",
        defaultFactory=_default_value(u"adviceStyle"),
        required=False,
    )

    form.write_permission(enable_advice_proposing_group_comment=u"PloneMeeting: Write risky config")
    enable_advice_proposing_group_comment = schema.Bool(
        title=_(u"PloneMeeting_label_enableAdviceProposingGroupComment", default=u"Enableadviceproposinggroupcomment"),
        description=_(u"enable_advice_proposing_group_comment_descr", default=u"EnableAdviceProposingGroupComment"),
        defaultFactory=_default_value(u"enableAdviceProposingGroupComment"),
        required=False,
    )

    form.write_permission(enforce_advice_mandatoriness=u"PloneMeeting: Write risky config")
    enforce_advice_mandatoriness = schema.Bool(
        title=_(u"PloneMeeting_label_enforceAdviceMandatoriness", default=u"Enforceadvicemandatoriness"),
        description=_(u"enforce_advice_mandatoriness_descr", default=u"EnforceAdviceMandatoriness"),
        defaultFactory=_default_value(u"enforceAdviceMandatoriness"),
        required=False,
    )

    form.write_permission(default_advice_hidden_during_redaction=u"PloneMeeting: Write risky config")
    form.widget('default_advice_hidden_during_redaction', CheckBoxFieldWidget)
    default_advice_hidden_during_redaction = schema.List(
        title=_(
            u"PloneMeeting_label_defaultAdviceHiddenDuringRedaction",
            default=u"Defaultadvicehiddenduringredaction",
        ),
        description=_(u"default_advice_hidden_during_redaction_descr", default=u"DefaultAdviceHiddenDuringRedaction"),
        value_type=schema.Choice(
            vocabulary=u"AdvicePortalTypes",
        ),
        defaultFactory=_default_value(u"defaultAdviceHiddenDuringRedaction"),
        required=False,
    )

    form.write_permission(transitions_reinitializing_delays=u"PloneMeeting: Write risky config")
    form.widget('transitions_reinitializing_delays', CheckBoxFieldWidget)
    transitions_reinitializing_delays = schema.List(
        title=_(u"PloneMeeting_label_transitionsReinitializingDelays", default=u"Transitionsreinitializingdelays"),
        description=_(u"transitions_reinitializing_delays_descr", default=u"TransitionsReinitializingDelays"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_transitions",
        ),
        defaultFactory=_default_value(u"transitionsReinitializingDelays"),
        required=False,
    )

    form.write_permission(historize_item_data_when_advice_is_given=u"PloneMeeting: Write risky config")
    historize_item_data_when_advice_is_given = schema.Bool(
        title=_(
            u"PloneMeeting_label_historizeItemDataWhenAdviceIsGiven",
            default=u"Historizeitemdatawhenadviceisgiven",
        ),
        description=_(u"historize_item_data_when_advice_is_given_descr", default=u"HistorizeItemDataWhenAdviceIsGiven"),
        defaultFactory=_default_value(u"historizeItemDataWhenAdviceIsGiven"),
        required=False,
    )

    form.write_permission(historize_advice_if_given_and_item_modified=u"PloneMeeting: Write risky config")
    historize_advice_if_given_and_item_modified = schema.Bool(
        title=_(
            u"PloneMeeting_label_historizeAdviceIfGivenAndItemModified",
            default=u"historizeadviceifgivenanditemmodified",
        ),
        description=_(
            u"historize_advice_if_given_and_item_modified_descr",
            default=u"historizeAdviceIfGivenAndItemModified",
        ),
        defaultFactory=_default_value(u"historizeAdviceIfGivenAndItemModified"),
        required=False,
    )

    form.write_permission(item_with_given_advice_is_not_deletable=u"PloneMeeting: Write risky config")
    item_with_given_advice_is_not_deletable = schema.Bool(
        title=_(u"PloneMeeting_label_itemWithGivenAdviceIsNotDeletable", default=u"Itemwithgivenadviceisnotdeletable"),
        description=_(u"item_with_given_advice_is_not_deletable_descr", default=u"ItemWithGivenAdviceIsNotDeletable"),
        defaultFactory=_default_value(u"itemWithGivenAdviceIsNotDeletable"),
        required=False,
    )

    form.write_permission(inherited_advice_removeable_by_adviser=u"PloneMeeting: Write risky config")
    inherited_advice_removeable_by_adviser = schema.Bool(
        title=_(
            u"PloneMeeting_label_inheritedAdviceRemoveableByAdviser",
            default=u"Inheritedadviceremoveablebyadviser",
        ),
        description=_(u"inherited_advice_removeable_by_adviser_descr", default=u"InheritedAdviceRemoveableByAdviser"),
        defaultFactory=_default_value(u"inheritedAdviceRemoveableByAdviser"),
        required=False,
    )

    form.write_permission(enable_add_quick_advice=u"PloneMeeting: Write risky config")
    enable_add_quick_advice = schema.Bool(
        title=_(u"PloneMeeting_label_enableAddQuickAdvice", default=u"Enableaddquickadvice"),
        description=_(u"enable_add_quick_advice_descr", default=u"EnableAddQuickAdvice"),
        defaultFactory=_default_value(u"enableAddQuickAdvice"),
        required=False,
    )

    form.write_permission(custom_advisers=u"PloneMeeting: Write risky config")
    form.widget('custom_advisers', DataGridFieldFactory)
    custom_advisers = DataGridField(
        title=_(u"PloneMeeting_label_customAdvisers", default=u"Customadvisers"),
        description=_(u"custom_advisers_descr", default=u"CustomAdvisers"),
        value_type=DictRow(schema=ICustomAdvisersRowSchema),
        defaultFactory=_default_value(u"customAdvisers"),
        required=False,
    )

    form.write_permission(power_advisers_groups=u"PloneMeeting: Write risky config")
    form.widget('power_advisers_groups', CheckBoxFieldWidget)
    power_advisers_groups = schema.List(
        title=_(u"PloneMeeting_label_powerAdvisersGroups", default=u"Poweradvisersgroups"),
        description=_(u"power_advisers_groups_descr", default=u"PowerAdvisersGroups"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_active_orgs_for_power_advisers",
        ),
        defaultFactory=_default_value(u"powerAdvisersGroups"),
        required=False,
    )

    form.write_permission(power_observers=WriteRiskyConfig)
    form.widget('power_observers', DataGridFieldFactory)
    power_observers = DataGridField(
        title=_(u"PloneMeeting_label_powerObservers", default=u"Powerobservers"),
        description=_(u"power_observers_descr", default=u"PowerObservers"),
        value_type=DictRow(schema=IPowerObserversRowSchema),
        defaultFactory=_default_value(u"powerObservers"),
        required=False,
    )

    form.write_permission(item_budget_infos_states=u"PloneMeeting: Write risky config")
    form.widget('item_budget_infos_states', CheckBoxFieldWidget)
    item_budget_infos_states = schema.List(
        title=_(u"PloneMeeting_label_itemBudgetInfosStates", default=u"Itembudgetinfosstates"),
        description=_(u"item_budget_infos_states_descr", default=u"ItemBudgetInfosStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemBudgetInfosStates"),
        required=False,
    )

    form.write_permission(item_groups_in_charge_states=u"PloneMeeting: Write risky config")
    form.widget('item_groups_in_charge_states', CheckBoxFieldWidget)
    item_groups_in_charge_states = schema.List(
        title=_(u"PloneMeeting_label_itemGroupsInChargeStates", default=u"Itemgroupsinchargestates"),
        description=_(u"item_groups_in_charge_states_descr", default=u"ItemGroupsInChargeStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemGroupsInChargeStates"),
        required=False,
    )

    form.write_permission(item_observers_states=u"PloneMeeting: Write risky config")
    form.widget('item_observers_states', CheckBoxFieldWidget)
    item_observers_states = schema.List(
        title=_(u"PloneMeeting_label_itemObserversStates", default=u"Itemobserversstates"),
        description=_(u"item_observers_states_descr", default=u"IitemObserversStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemObserversStates"),
        required=False,
    )

    form.write_permission(selectable_copy_groups=u"PloneMeeting: Write risky config")
    form.widget('selectable_copy_groups', CheckBoxFieldWidget)
    selectable_copy_groups = schema.List(
        title=_(u"PloneMeeting_label_selectableCopyGroups", default=u"Selectablecopygroups"),
        description=_(u"selectable_copy_groups_descr", default=u"SelectableCopyGroups"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_copy_groups",
        ),
        defaultFactory=_default_value(u"selectableCopyGroups"),
        required=False,
    )

    form.write_permission(item_copy_groups_states=u"PloneMeeting: Write risky config")
    form.widget('item_copy_groups_states', CheckBoxFieldWidget)
    item_copy_groups_states = schema.List(
        title=_(u"PloneMeeting_label_itemCopyGroupsStates", default=u"Itemcopygroupsstates"),
        description=_(u"item_copy_groups_states_descr", default=u"ItemCopyGroupsStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemCopyGroupsStates"),
        required=False,
    )

    form.write_permission(selectable_restricted_copy_groups=u"PloneMeeting: Write risky config")
    form.widget('selectable_restricted_copy_groups', CheckBoxFieldWidget)
    selectable_restricted_copy_groups = schema.List(
        title=_(u"PloneMeeting_label_selectableRestrictedCopyGroups", default=u"Selectablerestrictedcopygroups"),
        description=_(u"selectable_restricted_copy_groups_descr", default=u"SelectableRestrictedCopyGroups"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_selectable_copy_groups",
        ),
        defaultFactory=_default_value(u"selectableRestrictedCopyGroups"),
        required=False,
    )

    form.write_permission(item_restricted_copy_groups_states=u"PloneMeeting: Write risky config")
    form.widget('item_restricted_copy_groups_states', CheckBoxFieldWidget)
    item_restricted_copy_groups_states = schema.List(
        title=_(u"PloneMeeting_label_itemRestrictedCopyGroupsStates", default=u"Itemrestrictedcopygroupsstates"),
        description=_(u"item_restricted_copy_groups_states_descr", default=u"ItemRestrictedCopyGroupsStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemRestrictedCopyGroupsStates"),
        required=False,
    )

    form.write_permission(hide_history_to=u"PloneMeeting: Write risky config")
    form.widget('hide_history_to', CheckBoxFieldWidget)
    hide_history_to = schema.List(
        title=_(u"PloneMeeting_label_hideHistoryTo", default=u"Hidehistoryto"),
        description=_(u"hide_history_to_descr", default=u"HideHistoryTo"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.config_hide_history_to_vocabulary",
        ),
        defaultFactory=_default_value(u"hideHistoryTo"),
        required=False,
    )

    form.write_permission(
        hide_item_history_comments_to_users_outside_proposing_group=u"PloneMeeting: Write risky config"
    )
    hide_item_history_comments_to_users_outside_proposing_group = schema.Bool(
        title=_(
            u"PloneMeeting_label_hideItemHistoryCommentsToUsersOutsideProposingGroup",
            default=u"Hideitemhistorycommentstousersoutsideproposinggroup",
        ),
        description=_(
            u"hide_item_history_comments_to_users_outside_proposing_group_descr",
            default=u"HideItemHistoryCommentsToUsersOutsideProposingGroup",
        ),
        defaultFactory=_default_value(u"hideItemHistoryCommentsToUsersOutsideProposingGroup"),
        required=False,
    )

    form.write_permission(hide_not_viewable_linked_items_to=u"PloneMeeting: Write risky config")
    form.widget('hide_not_viewable_linked_items_to', CheckBoxFieldWidget)
    hide_not_viewable_linked_items_to = schema.List(
        title=_(u"PloneMeeting_label_hideNotViewableLinkedItemsTo", default=u"Hidenotviewablelinkeditemsto"),
        description=_(u"hide_not_viewable_linked_items_to_descr", default=u"HideNotViewableLinkedItemsTo"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_power_observers_types",
        ),
        defaultFactory=_default_value(u"hideNotViewableLinkedItemsTo"),
        required=False,
    )

    form.write_permission(restrict_access_to_secret_items=u"PloneMeeting: Write risky config")
    restrict_access_to_secret_items = schema.Bool(
        title=_(u"PloneMeeting_label_restrictAccessToSecretItems", default=u"Restrictaccesstosecretitems"),
        description=_(u"restrict_access_to_secret_items_descr", default=u"RestrictAccessToSecretItems"),
        defaultFactory=_default_value(u"restrictAccessToSecretItems"),
        required=False,
    )

    form.write_permission(restrict_access_to_secret_items_to=u"PloneMeeting: Write risky config")
    form.widget('restrict_access_to_secret_items_to', CheckBoxFieldWidget)
    restrict_access_to_secret_items_to = schema.List(
        title=_(u"PloneMeeting_label_restrictAccessToSecretItemsTo", default=u"Restrictaccesstosecretitemsto"),
        description=_(u"restrict_access_to_secret_items_to_descr", default=u"RestrictAccessToSecretItemsTo"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_power_observers_types",
        ),
        defaultFactory=_default_value(u"restrictAccessToSecretItemsTo"),
        required=False,
    )

    form.write_permission(annex_restrict_shown_and_editable_attributes=u"PloneMeeting: Write risky config")
    form.widget('annex_restrict_shown_and_editable_attributes', CheckBoxFieldWidget)
    annex_restrict_shown_and_editable_attributes = schema.List(
        title=_(
            u"PloneMeeting_label_annexRestrictShownAndEditableAttributes",
            default=u"Annexrestrictshownandeditableattributes",
        ),
        description=_(
            u"annex_restrict_shown_and_editable_attributes_descr",
            default=u"AnnexRestrictShownAndEditableAttributes",
        ),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.annex_restrict_shown_and_editable_attributes_vocabulary",
        ),
        defaultFactory=_default_value(u"annexRestrictShownAndEditableAttributes"),
        required=False,
    )

    form.write_permission(owner_may_delete_annex_decision=u"PloneMeeting: Write risky config")
    owner_may_delete_annex_decision = schema.Bool(
        title=_(u"PloneMeeting_label_ownerMayDeleteAnnexDecision", default=u"Ownermaydeleteannexdecision"),
        description=_(u"owner_may_delete_annex_decision_descr", default=u"OwnerMayDeleteAnnexDecision"),
        defaultFactory=_default_value(u"ownerMayDeleteAnnexDecision"),
        required=False,
    )

    form.write_permission(annex_editor_may_insert_barcode=u"PloneMeeting: Write risky config")
    annex_editor_may_insert_barcode = schema.Bool(
        title=_(u"PloneMeeting_label_annexEditorMayInsertBarcode", default=u"Annexeditormayinsertbarcode"),
        description=_(u"annex_editor_may_insert_barcode_descr", default=u"AnnexEditorMayInsertBarcode"),
        defaultFactory=_default_value(u"annexEditorMayInsertBarcode"),
        required=False,
    )

    form.write_permission(item_annex_confidential_visible_for=u"PloneMeeting: Write risky config")
    form.widget('item_annex_confidential_visible_for', CheckBoxFieldWidget)
    item_annex_confidential_visible_for = schema.List(
        title=_(u"PloneMeeting_label_itemAnnexConfidentialVisibleFor", default=u"Itemannexconfidentialvisiblefor"),
        description=_(u"item_annex_confidential_visible_for_descr", default=u"ItemAnnexConfidentialVisibleFor"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_attribute_visible_for",
        ),
        defaultFactory=_default_value(u"itemAnnexConfidentialVisibleFor"),
        required=False,
    )

    form.write_permission(advice_annex_confidential_visible_for=u"PloneMeeting: Write risky config")
    form.widget('advice_annex_confidential_visible_for', CheckBoxFieldWidget)
    advice_annex_confidential_visible_for = schema.List(
        title=_(u"PloneMeeting_label_adviceAnnexConfidentialVisibleFor", default=u"Adviceannexconfidentialvisiblefor"),
        description=_(u"advice_annex_confidential_visible_for_descr", default=u"AdviceAnnexConfidentialVisibleFor"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_advice_annex_confidential_visible_for",
        ),
        defaultFactory=_default_value(u"adviceAnnexConfidentialVisibleFor"),
        required=False,
    )

    form.write_permission(meeting_annex_confidential_visible_for=u"PloneMeeting: Write risky config")
    form.widget('meeting_annex_confidential_visible_for', CheckBoxFieldWidget)
    meeting_annex_confidential_visible_for = schema.List(
        title=_(
            u"PloneMeeting_label_meetingAnnexConfidentialVisibleFor",
            default=u"Meetingannexconfidentialvisiblefor",
        ),
        description=_(u"meeting_annex_confidential_visible_for_descr", default=u"meetingAnnexConfidentialVisibleFor"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_meeting_annex_confidential_visible_for",
        ),
        defaultFactory=_default_value(u"meetingAnnexConfidentialVisibleFor"),
        required=False,
    )

    form.write_permission(enable_advice_confidentiality=u"PloneMeeting: Write risky config")
    enable_advice_confidentiality = schema.Bool(
        title=_(u"PloneMeeting_label_enableAdviceConfidentiality", default=u"Enableadviceconfidentiality"),
        description=_(u"enable_advice_confidentiality_descr", default=u"EnableAdviceConfidentiality"),
        defaultFactory=_default_value(u"enableAdviceConfidentiality"),
        required=False,
    )

    form.write_permission(advice_confidentiality_default=u"PloneMeeting: Write risky config")
    advice_confidentiality_default = schema.Bool(
        title=_(u"PloneMeeting_label_adviceConfidentialityDefault", default=u"Adviceconfidentialitydefault"),
        description=_(u"advice_confidentiality_default_descr", default=u"AdviceConfidentialityDefault"),
        defaultFactory=_default_value(u"adviceConfidentialityDefault"),
        required=False,
    )

    form.write_permission(advice_confidential_for=u"PloneMeeting: Write risky config")
    form.widget('advice_confidential_for', CheckBoxFieldWidget)
    advice_confidential_for = schema.List(
        title=_(u"PloneMeeting_label_adviceConfidentialFor", default=u"Adviceconfidentialfor"),
        description=_(u"advice_confidential_for_descr", default=u"AdviceConfidentialFor"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_power_observers_types",
        ),
        defaultFactory=_default_value(u"adviceConfidentialFor"),
        required=False,
    )

    form.write_permission(labels_config=WriteRiskyConfig)
    form.widget('labels_config', DataGridFieldFactory)
    labels_config = DataGridField(
        title=_(u"PloneMeeting_label_labelsConfig", default=u"Labelsconfig"),
        description=_(u"labels_config_descr", default=u"LabelsConfig"),
        value_type=DictRow(schema=ILabelsConfigRowSchema),
        defaultFactory=_default_value(u"labelsConfig"),
        required=False,
    )

    form.write_permission(item_internal_notes_editable_by=u"PloneMeeting: Write risky config")
    form.widget('item_internal_notes_editable_by', CheckBoxFieldWidget)
    item_internal_notes_editable_by = schema.List(
        title=_(u"PloneMeeting_label_itemInternalNotesEditableBy", default=u"Iteminternalnoteseditableby"),
        description=_(u"item_internal_notes_editable_by_descr", default=u"ItemInternalNotesEditableByMeetingManagers"),
        value_type=schema.Choice(
            vocabulary=(
                u"Products.PloneMeeting.vocabularies."
                u"meeting_config_list_item_attribute_visible_for_with_meeting_managers"
            ),
        ),
        defaultFactory=_default_value(u"itemInternalNotesEditableBy"),
        required=False,
    )

    form.write_permission(item_fields_config=WriteRiskyConfig)
    form.widget('item_fields_config', DataGridFieldFactory)
    item_fields_config = DataGridField(
        title=_(u"PloneMeeting_label_itemFieldsConfig", default=u"Itemfieldsconfig"),
        description=_(u"item_fields_config_descr", default=u"ItemFieldsConfig"),
        value_type=DictRow(schema=IItemFieldsConfigRowSchema),
        defaultFactory=_default_value(u"itemFieldsConfig"),
        required=False,
    )

    form.write_permission(using_groups=u"PloneMeeting: Write risky config")
    form.widget('using_groups', CheckBoxFieldWidget)
    using_groups = schema.List(
        title=_(u"PloneMeeting_label_configUsingGroups", default=u"Usinggroups"),
        description=_(u"config_using_groups_descr", default=u"UsingGroups"),
        value_type=schema.Choice(
            vocabulary=u"collective.contact.plonegroup.browser.settings.SortedSelectedOrganizationsElephantVocabulary",
        ),
        defaultFactory=_default_value(u"usingGroups"),
        required=False,
    )

    form.write_permission(ordered_committee_contacts=u"PloneMeeting: Write risky config")
    form.widget('ordered_committee_contacts', OrderedSelectFieldWidget)
    ordered_committee_contacts = schema.List(
        title=_(u"PloneMeeting_label_orderedCommitteeContacts", default=u"Orderedcommitteecontacts"),
        description=_(u"ordered_committee_contacts_descr", default=u"OrderedCommitteeContacts"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.every_heldpositions_vocabulary",
        ),
        defaultFactory=_default_value(u"orderedCommitteeContacts"),
        required=False,
    )

    form.write_permission(item_committees_states=u"PloneMeeting: Write risky config")
    form.widget('item_committees_states', CheckBoxFieldWidget)
    item_committees_states = schema.List(
        title=_(u"PloneMeeting_label_itemCommitteesStates", default=u"Itemcommitteesstates"),
        description=_(u"item_committees_states_descr", default=u"ItemCommitteesStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemCommitteesStates"),
        required=False,
    )

    form.write_permission(item_committees_view_states=u"PloneMeeting: Write risky config")
    form.widget('item_committees_view_states', CheckBoxFieldWidget)
    item_committees_view_states = schema.List(
        title=_(u"PloneMeeting_label_itemCommitteesViewStates", default=u"Itemcommitteesviewstates"),
        description=_(u"item_committees_view_states_descr", default=u"ItemCommitteesViewStates"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_item_states",
        ),
        defaultFactory=_default_value(u"itemCommitteesViewStates"),
        required=False,
    )

    form.write_permission(committees=u"PloneMeeting: Write risky config")
    form.widget('committees', DataGridFieldFactory)
    committees = DataGridField(
        title=_(u"PloneMeeting_label_committees", default=u"Committees"),
        description=_(u"committees_descr", default=u"Committees"),
        value_type=DictRow(schema=ICommitteesRowSchema),
        defaultFactory=_default_value(u"committees"),
        required=False,
    )

    form.write_permission(use_votes=u"PloneMeeting: Write risky config")
    use_votes = schema.Bool(
        title=_(u"PloneMeeting_label_useVotes", default=u"Usevotes"),
        description=_(u"use_votes_descr", default=u"UseVotes"),
        defaultFactory=_default_value(u"useVotes"),
        required=False,
    )

    form.write_permission(votes_encoder=u"PloneMeeting: Write risky config")
    form.widget('votes_encoder', CheckBoxFieldWidget)
    votes_encoder = schema.List(
        title=_(u"PloneMeeting_label_votesEncoder", default=u"Votesencoder"),
        description=_(u"votes_encoder_descr", default=u"VotesEncoder"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_votes_encoders",
        ),
        defaultFactory=_default_value(u"votesEncoder"),
        required=False,
    )

    form.write_permission(used_poll_types=u"PloneMeeting: Write risky config")
    form.widget('used_poll_types', OrderedSelectFieldWidget)
    used_poll_types = schema.List(
        title=_(u"PloneMeeting_label_usedPollTypes", default=u"Usedpolltypes"),
        description=_(u"used_poll_types_descr", default=u"UsedPollTypes"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_poll_types",
        ),
        defaultFactory=_default_value(u"usedPollTypes"),
        required=False,
    )

    form.write_permission(default_poll_type=u"PloneMeeting: Write risky config")
    form.widget('default_poll_type', SelectFieldWidget)
    default_poll_type = schema.Choice(
        title=_(u"PloneMeeting_label_defaultPollType", default=u"Defaultpolltype"),
        description=_(u"default_poll_type_descr", default=u"DefaultPollType"),
        vocabulary=u"Products.PloneMeeting.vocabularies.meeting_config_list_poll_types",
        defaultFactory=_default_value(u"defaultPollType"),
        required=False,
    )

    form.write_permission(used_vote_values=u"PloneMeeting: Write risky config")
    form.widget('used_vote_values', OrderedSelectFieldWidget)
    used_vote_values = schema.List(
        title=_(u"PloneMeeting_label_usedVoteValues", default=u"Usedvotevalues"),
        description=_(u"used_vote_values_descr", default=u"UsedVoteValues"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.allvotevaluesvocabulary",
        ),
        defaultFactory=_default_value(u"usedVoteValues"),
        required=False,
    )

    form.write_permission(first_linked_vote_used_vote_values=u"PloneMeeting: Write risky config")
    form.widget('first_linked_vote_used_vote_values', OrderedSelectFieldWidget)
    first_linked_vote_used_vote_values = schema.List(
        title=_(u"PloneMeeting_label_firstLinkedVoteUsedVoteValues", default=u"Firstlinkedvoteusedvotevalues"),
        description=_(u"first_linked_vote_used_vote_values_descr", default=u"FirstLinkedVoteUsedVoteValues"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.allvotevaluesvocabulary",
        ),
        defaultFactory=_default_value(u"firstLinkedVoteUsedVoteValues"),
        required=False,
    )

    form.write_permission(next_linked_votes_used_vote_values=u"PloneMeeting: Write risky config")
    form.widget('next_linked_votes_used_vote_values', OrderedSelectFieldWidget)
    next_linked_votes_used_vote_values = schema.List(
        title=_(u"PloneMeeting_label_nextLinkedVotesUsedVoteValues", default=u"nextlinkedvotesusedvotevalues"),
        description=_(u"next_linked_votes_used_vote_values_descr", default=u"NextLinkedVotesUsedVoteValues"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.allvotevaluesvocabulary",
        ),
        defaultFactory=_default_value(u"nextLinkedVotesUsedVoteValues"),
        required=False,
    )

    form.write_permission(vote_condition=u"PloneMeeting: Write risky config")
    vote_condition = schema.TextLine(
        title=_(u"PloneMeeting_label_voteCondition", default=u"Votecondition"),
        description=_(u"vote_condition_descr", default=u"VoteCondition"),
        defaultFactory=_default_value(u"voteCondition"),
        required=False,
    )

    form.write_permission(votes_result_tal_expr=u"PloneMeeting: Write risky config")
    votes_result_tal_expr = schema.TextLine(
        title=_(u"PloneMeeting_label_votesResultTALExpr", default=u"Votesresulttalexpr"),
        description=_(u"votes_result_tal_expr_descr", default=u"VotesResultTALExpr"),
        defaultFactory=_default_value(u"votesResultTALExpr"),
        required=False,
    )

    form.write_permission(display_voting_group=u"PloneMeeting: Write risky config")
    display_voting_group = schema.Bool(
        title=_(u"PloneMeeting_label_displayVotingGroup", default=u"Displayvotinggroup"),
        description=_(u"display_voting_group_descr", default=u"DisplayVotingGroup"),
        defaultFactory=_default_value(u"displayVotingGroup"),
        required=False,
    )

    form.write_permission(meeting_item_templates_to_store_as_annex=u"PloneMeeting: Write risky config")
    form.widget('meeting_item_templates_to_store_as_annex', CheckBoxFieldWidget)
    meeting_item_templates_to_store_as_annex = schema.List(
        title=_(
            u"PloneMeeting_label_meetingItemTemplatesToStoreAsAnnex",
            default=u"Meetingitemtemplatestostoreasannex",
        ),
        description=_(u"meeting_item_templates_to_store_as_annex_descr", default=u"MeetingItemTemplatesToStoreAsAnnex"),
        value_type=schema.Choice(
            vocabulary=u"Products.PloneMeeting.vocabularies.itemtemplatesstorableasannexvocabulary",
        ),
        defaultFactory=_default_value(u"meetingItemTemplatesToStoreAsAnnex"),
        required=False,
    )

    model.fieldset(
        u"assembly_and_signatures",
        label=_(u"fieldset_meeting_config_assembly_and_signatures", default=u"Assembly and signatures"),
        fields=[
            u"assembly",
            u"assembly_staves",
            u"signatures",
            u"certified_signatures",
            u"ordered_contacts",
            u"ordered_item_initiators",
            u"selectable_redefined_position_types",
        ],
    )

    model.fieldset(
        u"data",
        label=_(u"fieldset_meeting_config_data", default=u"Data"),
        fields=[
            u"used_item_attributes",
            u"historized_item_attributes",
            u"record_item_history_states",
            u"used_meeting_attributes",
            u"ordered_associated_organizations",
            u"ordered_groups_in_charge",
            u"include_groups_in_charge_defined_on_proposing_group",
            u"include_groups_in_charge_defined_on_category",
            u"to_discuss_set_on_item_insert",
            u"to_discuss_default",
            u"to_discuss_late_default",
            u"item_reference_format",
            u"compute_item_reference_for_items_out_of_meeting",
            u"inserting_methods_on_add_item",
            u"selectable_privacies",
            u"all_item_tags",
            u"sort_all_item_tags",
            u"item_fields_to_keep_config_sorting_for",
            u"list_types",
            u"xhtml_transform_fields",
            u"xhtml_transform_types",
            u"validation_deadline_default",
            u"freeze_deadline_default",
            u"meeting_configs_to_clone_to",
            u"item_auto_sent_to_other_mc_states",
            u"item_manual_sent_to_other_mc_states",
            u"contents_kept_on_sent_to_other_mc",
            u"advices_kept_on_sent_to_other_mc",
            u"enabled_item_actions",
            u"annex_to_print_mode",
            u"keep_original_to_print_of_cloned_items",
            u"remove_annexes_previews_on_meeting_closure",
            u"css_transforms",
        ],
    )

    model.fieldset(
        u"workflow",
        label=_(u"fieldset_meeting_config_workflow", default=u"Workflow"),
        fields=[
            u"item_workflow",
            u"item_conditions_interface",
            u"item_actions_interface",
            u"meeting_workflow",
            u"meeting_conditions_interface",
            u"meeting_actions_interface",
            u"workflow_adaptations",
            u"item_wf_validation_levels",
            u"transitions_to_confirm",
            u"on_transition_field_transforms",
            u"on_meeting_transition_item_action_to_execute",
            u"meeting_present_item_when_no_current_meeting_states",
            u"item_preferred_meeting_states",
        ],
    )

    model.fieldset(
        u"gui",
        label=_(u"fieldset_meeting_config_gui", default=u"GUI"),
        fields=[
            u"item_columns",
            u"available_items_list_visible_columns",
            u"items_list_visible_columns",
            u"item_actions_column_config",
            u"meeting_columns",
            u"enabled_annexes_batch_actions",
            u"display_available_items_to",
            u"redirect_to_next_meeting",
            u"items_visible_fields",
            u"items_not_viewable_visible_fields",
            u"items_not_viewable_visible_fields_tal_expr",
            u"items_list_visible_fields",
            u"max_shown_meetings",
            u"to_do_list_searches",
            u"dashboard_items_listings_filters",
            u"dashboard_meeting_available_items_filters",
            u"dashboard_meeting_linked_items_filters",
            u"dashboard_meetings_listings_filters",
            u"groups_hidden_in_dashboard_filter",
            u"users_hidden_in_dashboard_filter",
            u"max_shown_listings",
            u"max_shown_available_items",
            u"max_shown_meeting_items",
        ],
    )

    model.fieldset(
        u"mail",
        label=_(u"fieldset_meeting_config_mail", default=u"Mail"),
        fields=[
            u"mail_mode",
            u"mail_item_events",
            u"mail_meeting_events",
        ],
    )

    model.fieldset(
        u"advices",
        label=_(u"fieldset_meeting_config_advices", default=u"Advices"),
        fields=[
            u"use_advices",
            u"used_advice_types",
            u"default_advice_type",
            u"selectable_advisers",
            u"selectable_adviser_users",
            u"item_advice_states",
            u"item_advice_edit_states",
            u"item_advice_view_states",
            u"keep_access_to_item_when_advice",
            u"enable_advice_invalidation",
            u"item_advice_invalidate_states",
            u"advice_style",
            u"enable_advice_proposing_group_comment",
            u"enforce_advice_mandatoriness",
            u"default_advice_hidden_during_redaction",
            u"transitions_reinitializing_delays",
            u"historize_item_data_when_advice_is_given",
            u"historize_advice_if_given_and_item_modified",
            u"item_with_given_advice_is_not_deletable",
            u"inherited_advice_removeable_by_adviser",
            u"enable_add_quick_advice",
            u"custom_advisers",
            u"power_advisers_groups",
            u"power_observers",
            u"item_budget_infos_states",
            u"item_groups_in_charge_states",
            u"item_observers_states",
            u"selectable_copy_groups",
            u"item_copy_groups_states",
            u"selectable_restricted_copy_groups",
            u"item_restricted_copy_groups_states",
            u"hide_history_to",
            u"hide_item_history_comments_to_users_outside_proposing_group",
            u"hide_not_viewable_linked_items_to",
            u"restrict_access_to_secret_items",
            u"restrict_access_to_secret_items_to",
            u"annex_restrict_shown_and_editable_attributes",
            u"owner_may_delete_annex_decision",
            u"annex_editor_may_insert_barcode",
            u"item_annex_confidential_visible_for",
            u"advice_annex_confidential_visible_for",
            u"meeting_annex_confidential_visible_for",
            u"enable_advice_confidentiality",
            u"advice_confidentiality_default",
            u"advice_confidential_for",
            u"labels_config",
            u"item_internal_notes_editable_by",
            u"item_fields_config",
            u"using_groups",
        ],
    )

    model.fieldset(
        u"committees",
        label=_(u"fieldset_meeting_config_committees", default=u"Committees"),
        fields=[
            u"ordered_committee_contacts",
            u"item_committees_states",
            u"item_committees_view_states",
            u"committees",
        ],
    )

    model.fieldset(
        u"votes",
        label=_(u"fieldset_meeting_config_votes", default=u"Votes"),
        fields=[
            u"use_votes",
            u"votes_encoder",
            u"used_poll_types",
            u"default_poll_type",
            u"used_vote_values",
            u"first_linked_vote_used_vote_values",
            u"next_linked_votes_used_vote_values",
            u"vote_condition",
            u"votes_result_tal_expr",
            u"display_voting_group",
        ],
    )

    model.fieldset(
        u"doc",
        label=_(u"fieldset_meeting_config_doc", default=u"Documents"),
        fields=[
            u"meeting_item_templates_to_store_as_annex",
        ],
    )
