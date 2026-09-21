/* Popups of PloneMeeting. They use the imio_modal helper of imio.helpers. */

// the advice add/edit popup
function adviceAddEdit() {
  imio_modal('a.link-overlay-pm-advice', {
    hidden: function (modal, element) {
      // unlock the advice, an add form has nothing to unlock
      var advice_url = $(element).attr('href');
      if (advice_url.indexOf('++add++meetingadvice') === -1) {
        // remove '/edit'
        advice_url = advice_url.slice(0, -5);
        $.ajax({url: advice_url + "/@@plone_lock_operations/safe_unlock", });
      }
    }
  });
}


// opening the advice preview from the advice tooltip
function advicePreview() {
  imio_modal('a.link-overlay-pm-preview-advice', {
    closeOnBackdrop: true,
    afterRender: function (modal, element) {
      // tooltipster for annexes
      categorizedChildsInfos({selector: 'div.meeting-advice-view .tooltipster-childs-infos', });
    }
  });
}

// the modal that displays the attendees or votes form
var pm_attendees_modal = null;

// opening the encode votes form
function manageAttendees() {
  imio_modal('a.link-overlay-pm-manage-attendees', {
    submit: 'helper',
    afterRender: function (modal, element) {
      pm_attendees_modal = modal;
      // odd even for datagridfield
      // need to add listing to table class
      $('table.datagridwidget-table-view', modal.$modalContent).addClass('listing');
      $('table tbody', modal.$modalContent).each(setoddeven);
      submitFormHelper(onsuccess=onsuccessManageAttendees);
    },
    hidden: function (modal, element) {
      var href = $(element).attr('href');
      selector = '.attendee-value';
      if (href.includes('item-encode-votes-form') || href.includes('encode_votes')) {
        selector = '.vote-value';
      }
      else if (href.includes('_attendee_form')) {
        selector = '.attendee-assembly';
      }
      else if (href.includes('_signatory_form')) {
        selector = '.attendee-signatory';
      }
      else if (href.includes('_nonattendee_form')) {
        selector = '.attendee-nonattendee';
      }
      highlight_attendees(selector);

      // reload votesResult
      if (href.includes('_votes_form')) {
        reloadVotesResult();
      }
    }
  });
}

function reloadVotesResult() {
    tags = $("div#marker-collapsible-field-votesResult");
    if (tags.length == 1) {
      loadContent(tags[0], load_view='@@display-collapsible-rich-field?field_name=votesResult');
    }
}

// refresh meeting attendees panel
function refresh_meeting_attendees() {
  tag = $("#collapsible-assembly-and-signatures div")[0];
  var timeStamp = new Date();
  result = loadContent(
    tag,
    load_view='@@load_meeting_assembly_and_signatures?cache_date=' + timeStamp,
    async=false,
    base_url=null,
    event_name="toggle_details_ajax_success");
  highlight_attendees();
}

// refresh item attendees panel
function refresh_attendees(highlight=null, click_cancel=false) {
  tag = $("#collapsible-assembly-and-signatures div")[0];
  var timeStamp = new Date();
  result = loadContent(
    tag,
    load_view='@@load_item_assembly_and_signatures?cache_date=' + timeStamp,
    async=false,
    base_url=null,
    event_name="toggle_details_ajax_success");
  if (click_cancel) {
    $('input#form-buttons-cancel').click();
  }
  if (highlight) {
    $.when(highlight_attendees(highlight));
  }
}
// highlight votes when it is refreshed
function highlight_attendees(highlight_selector='') {
  $.when($("#collapsible-assembly-and-signatures table tr td" + highlight_selector).effect(
    'highlight', {}, 2000));
  $.when($("#collapsible-assembly-and-signatures dl.portalMessage.warning").effect(
    'bounce', {}, 1000));
}

function onsuccessManageAttendees(data) {
  if (data.byteLength) {
    // data is an arraybuffer, convert it to str
    data_str = new TextDecoder().decode(data);
    if (pm_attendees_modal) {
      pm_attendees_modal.redraw(data_str, pm_attendees_modal.options);
    }
  }
  else {
    refresh_attendees(highlight=null, click_cancel=true);
  }
}

// the content history popup
function contentHistory() {
  imio_modal('.contentHistory a', {closeOnBackdrop: true});
}

// the duplicate item action, the form redirects to the new item
function duplicateItem() {
  imio_modal('.apButtonAction_form_duplicate', {redirect: true});
}

// the item export pdf action
function itemExportPDF() {
  imio_modal('.apButtonAction_form_export_pdf', {
    submit: 'native',
    afterRender: function (modal, element) {
      // the browser downloads the file in a new tab, close the popup
      var form = $("form#form", modal.$modalContent);
      form.attr('target', '_blank');
      $("input#form-buttons-apply_export_pdf", modal.$modalContent).click(function (e) {
        setTimeout(function () { modal.hide(); }, 100);
      });
    }
  });
}

// common popups
function pmCommonOverlays(selector_prefix='') {
  // Every common popups, must stay at the bottom of every defined popups!!!
  // Or it is taken before others because selector matches
  imio_modal(selector_prefix + 'a.link-overlay-pm');
  // Info popups that may be closed whenever clicking outside
  imio_modal(selector_prefix + 'a.link-overlay-pm-info', {closeOnBackdrop: true});
}



jQuery(document).ready(function($) {
    usersGroupInfos();
    groupedConfigs();
    advicesInfos();
    adviceAddEdit();
    listTypeChange();
    pollTypeChange();
    emergencyChange();
    completenessChange();
    availableMailingLists();
    duplicateItem();
    itemExportPDF();

    // inserting methods infos on meeting_view
    tooltipster_helper(selector='.tooltipster-inserting-methods-helper-msg',
                       view_name='@@display-inserting-methods-helper-msg',
                       data_parameters=[],
                       options={position: 'bottom',
                                trigger: 'click'});
    addCompleteOrQuickMeetingAdvice();
    pmCommonOverlays();
});

function attendeesInfos() {
    // item absents on item/meeting
    tooltipster_helper(selector='.tooltipster-meeting-item-not-present',
                       view_name='@@display-meeting-item-not-present',
                       data_parameters=['not_present_uid', 'not_present_type']);
    // item signatories on item/meeting
    tooltipster_helper(selector='.tooltipster-meeting-item-signatories',
                       view_name='@@display-meeting-item-signatories',
                       data_parameters=['signatory_uid']);
    // item redefined position on item/meeting
    tooltipster_helper(selector='.tooltipster-meeting-item-redefined-position',
                       view_name='@@display-meeting-item-redefined-position',
                       data_parameters=['attendee_uid']);
}

// prepare overlays and tooltipsters in dashboards
function initializeDashboard(){
    categorizedChildsInfos();
    advicesInfos();
    adviceAddEdit();
    contentHistory();
    duplicateItem();
    itemExportPDF();
    pmCommonOverlays();
    listTypeChange();
    actionsPanelTooltipster();
    addCompleteOrQuickMeetingAdvice();
}

function initializeAdvicePopup(instance) {
    // configure the triggerClose options after popup has been opened
    // this avoid weird behavior where in this case, just quickly hovering
    // the tooltipster would open it
    instance.__options.triggerClose = {click: true, tap: true, };

    // when an advice popup tooltipster is opened, we need to init JS on it
    categorizedChildsInfos({selector: 'td.advice_annexes .tooltipster-childs-infos', });
    adviceAddEdit();
    advicePreview();
    inheritedItemInfos();
    usersGroupInfos();
    adviceChangeDelay();
    contentHistory();
    // overlay for remove inherited advice
    pmCommonOverlays(selector_prefix='div.advice_infos_tooltipster ');
    initReadmore();
}

function overOverlays(){
  // used by popups displayed over another popup
  imio_modal('a.link-overlay-pm-over');
}


function editAnnex(){
  imio_modal('a.link-overlay-pm-annex', {
    afterRender: function (modal, element) {
      initializeIconifiedCategoryWidget();
    },
    hidden: function (modal, element) {
      // unlock the annex, an add form has nothing to unlock
      var obj_url = $(element).attr('href');
      if (obj_url.indexOf('++add++annex') === -1) {
        // remove '/edit'
        obj_url = obj_url.slice(0, -5);
        $.ajax({url: obj_url + "/@@plone_lock_operations/safe_unlock", });
      }
    }
  });
}

function listTypeChange() {
    // listType change on meetingitem_view
    tooltipster_helper(selector='.tooltipster-item-listtype-change',
                       view_name='@@item-listtype',
                       data_parameters=[],
                       options={position: 'right'});
}

function pollTypeChange() {
    // pollType change on meetingitem_view
    tooltipster_helper(selector='.tooltipster-item-polltype-change',
                       view_name='@@item-polltype',
                       data_parameters=[],
                       options={});
}

function votePollTypeChange() {
    // vote pollType change on meetingitem_view
    tooltipster_helper(selector='.tooltipster-item-vote-polltype-change',
                       view_name='@@item-vote-polltype',
                       data_parameters=['vote_number:int'],
                       options={});
}

function emergencyChange() {
    // emergency change on meetingitem_view
    tooltipster_helper(selector='.tooltipster-item-emergency-change',
                       view_name='@@item-emergency',
                       data_parameters=[],
                       options={position: 'bottom',
                                functionReady_callback: pmCommonOverlays});
}

function completenessChange() {
    // emergency change on meetingitem_view
    tooltipster_helper(selector='.tooltipster-item-completeness-change',
                       view_name='@@item-completeness',
                       data_parameters=[],
                       options={position: 'bottom',
                                functionReady_callback: pmCommonOverlays});
}

function availableMailingLists() {
    // mailing lists displayed on a POD template in the generation links viewlet
    tooltipster_helper(selector='.tooltipster-available-mailing-lists',
                       view_name='@@available-mailing-lists',
                       data_parameters=['template_uid', 'output_format'],
                       options={trigger: 'click', position: 'bottom'});
}

function inheritedItemInfos() {
    tooltipster_helper(selector='.tooltipster-inherited-advice',
                       view_name='@@display-inherited-item-infos',
                       data_parameters=['advice_id'],
                       options={maxWidth: 750});
}

function usersGroupInfos() {
    tooltipster_helper(selector='.tooltipster-group-users',
                       view_name='@@display-group-users',
                       data_parameters=['group_ids:json'],
                       options={position: 'bottom'});
}

function adviceChangeDelay() {
    tooltipster_helper(selector='.tooltipster-advice-change-delay',
                       view_name='@@advice-available-delays',
                       data_parameters=['advice'],
                       options={functionReady_callback: pmCommonOverlays});
}

function addCompleteOrQuickMeetingAdvice() {
    tooltipster_helper(selector='.tooltipster-advice-add-complete-quick',
                       view_name='@@advice-add-complete-quick',
                       data_parameters=[],
                       options={zIndex: 50,
                                minWidth: 350,
                                functionReady_callback: adviceAddEdit,
                                close_other_tips: true});
}

function positionAdvicePopup(instance, helper, position) {
    // position to 50px of the top
    if (position.coord.top < 0) {
        position.coord.top = 0;
    }
    return position;
}

function advicesInfos() {
    // values are adapted when used in a dashboard to avoid negative top position
    // may occur with the available items dashboard or when screen zoomed to much
    dashboard_position = 'left';
    position_callback = null;
    if ($('table#faceted_table').length) {
        dashboard_position = ['left'];
        position_callback = positionAdvicePopup;
    }
    // displayed in faceted dashboard
    tooltipster_helper(
      selector='div#faceted-form a.tooltipster-advices-infos',
      view_name='@@advices-icons-infos',
      data_parameters=['adviceType'],
      options={zIndex: 50,
               position: dashboard_position,
               functionReady_callback: initializeAdvicePopup,
               passInstanceToCallback: true,
               functionPosition_callback: position_callback,
               minWidth: 750,
               maxWidth: 750,
               close_other_tips: true});
    // displayed on item view, displayed bottom to deal with readmorable
    tooltipster_helper(
      selector='a.tooltipster-advices-infos',
      view_name='@@advices-icons-infos',
      data_parameters=['adviceType'],
      options={zIndex: 50,
               position: 'bottom',
               functionReady_callback: initializeAdvicePopup,
               passInstanceToCallback: true,
               minWidth: 750,
               maxWidth: 750,
               close_other_tips: true});
}

function groupedConfigs() {
    tooltipster_helper(selector='li[id*="portaltab-mc_config_group_"] a',
                       view_name='@@display-grouped-configs',
                       data_parameters=['config_group'],
                       options={
                        theme: 'tooltipster-light sub-portaltab',
                        arrow: false,
                        functionPosition_callback: function (instance, helper, position){
                            position.coord.top -= 6;return position;},
                        });
}

function initializeActionsPanelTooltipster_callback() {
    jQuery(function($) {
        initializeOverlays();
        preventDefaultClick();
        duplicateItem();
        itemExportPDF();
    });
}

function actionsPanelTooltipster() {
    tooltipster_helper(
        selector='.tooltipster-actions-panel',
        view_name='@@facade_actions_panel',
        data_parameters=['showHistory:boolean', 'showActions'],
        options={
         position: 'bottom',
         functionReady_callback: initializeActionsPanelTooltipster_callback,
         close_other_tips: true, });
}
