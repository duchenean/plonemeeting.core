# -*- coding: utf-8 -*-
#
# File: ToolPloneMeeting.py
#
# GNU General Public License (GPL)
#
from __future__ import absolute_import, print_function

from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from App.class_init import InitializeClass
from Acquisition import aq_base
from Acquisition import aq_inner
from collections import OrderedDict
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import get_organizations
from collective.contact.plonegroup.utils import get_person_from_userid
from collective.contact.plonegroup.utils import get_plone_group_id
# P6 migration: zc.async dropped, conversion runs inline. Reimplement as background job in Stage D.
# from collective.documentviewer.async import queueJob
from collective.documentviewer.convert import Converter
from collective.documentviewer.settings import GlobalSettings
from collective.iconifiedcategory.behaviors.iconifiedcategorization import IconifiedCategorization
from collective.iconifiedcategory.interfaces import IIconifiedPreview
from collective.iconifiedcategory.utils import calculate_category_id
from collective.iconifiedcategory.utils import get_categories
from collective.iconifiedcategory.utils import get_categorized_elements
from collective.iconifiedcategory.utils import get_category_object
from collective.iconifiedcategory.utils import get_config_root
from collective.iconifiedcategory.utils import update_all_categorized_elements
from datetime import datetime
from DateTime import DateTime
from ftw.labels.labeling import ANNOTATION_KEY as FTW_LABELS_ANNOTATION_KEY
from imio.actionspanel.utils import unrestrictedRemoveGivenObject
from imio.helpers.cache import cleanForeverCache
from imio.helpers.cache import cleanRamCache
from imio.helpers.cache import cleanVocabularyCacheFor
from imio.helpers.cache import get_cachekey_volatile
from imio.helpers.cache import get_current_user_id
from imio.helpers.cache import get_plone_groups_for_user
from imio.helpers.cache import invalidate_cachekey_volatile_for
from imio.helpers.content import get_vocab
from imio.helpers.content import uuidsToObjects
from imio.helpers.security import check_zope_admin
from imio.helpers.security import fplog
from imio.history.utils import add_event_to_wf_history
from imio.migrator.utils import end_time
from OFS import CopySupport
from OFS.OrderedFolder import OrderedFolder
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from persistent.mapping import PersistentMapping
from plone import api
from plone.memoize import ram
from plonemeeting.core.compat import DisplayList
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import UniqueObject
from Products.CMFPlone.utils import safe_unicode
from Products.CPUtils.Extensions.utils import remove_generated_previews
from plonemeeting.core import logger
from plonemeeting.core.config import ADD_CONTENT_PERMISSIONS
from plonemeeting.core.config import DEFAULT_COPIED_FIELDS
from plonemeeting.core.config import MEETING_CONFIG
from plonemeeting.core.config import MEETINGMANAGERS_GROUP_SUFFIX
from plonemeeting.core.config import PloneMeetingError
from plonemeeting.core.config import PMMessageFactory as _
from plonemeeting.core.config import PROJECTNAME
from plonemeeting.core.config import PY_DATETIME_WEEKDAYS
from plonemeeting.core.config import ROOT_FOLDER
from plonemeeting.core.config import SENT_TO_OTHER_MC_ANNOTATION_BASE_KEY
from plonemeeting.core.content.content_category import ANNEX_NOT_KEPT
from plonemeeting.core.content.meeting import IMeeting
from plonemeeting.core.content.meeting import Meeting
from plonemeeting.core.indexes import DELAYAWARE_ROW_ID_PATTERN
from plonemeeting.core.interfaces import IMeetingItem
from plonemeeting.core.MeetingItem import MeetingItem
from plonemeeting.core.model.adaptations import _performAdviceWorkflowAdaptations
from plonemeeting.core.profiles import PloneMeetingConfiguration
from plonemeeting.core.utils import configure_advice_dx_localroles_for
from plonemeeting.core.utils import duplicate_workflow
from plonemeeting.core.utils import get_annexes
from plonemeeting.core.utils import getCustomAdapter
from plonemeeting.core.utils import isPowerObserverForCfg
from plonemeeting.core.utils import monthsIds
from plonemeeting.core.utils import notifyModifiedAndReindex
from plonemeeting.core.utils import org_id_to_uid
from plonemeeting.core.utils import reindex_object
from plonemeeting.core.utils import workday
from Products.ZCatalog.ProgressHandler import ZLogHandler
from ZODB.POSException import ConflictError
from zope.annotation.interfaces import IAnnotations
from zope.i18n import translate
from zope.interface import implements

from . import interfaces
import OFS.Moniker
import six
import time


__author__ = """Gaetan DELANNAY <gaetan.delannay@geezteem.com>, Gauthier BASTIEN
<g.bastien@imio.be>, Stephan GEULETTE <s.geulette@imio.be>"""
__docformat__ = 'plaintext'

defValues = PloneMeetingConfiguration.get()
# This way, I get the default values for some MeetingConfig fields,
# that are defined in a unique place: the MeetingConfigDescriptor class, used
# for importing profiles.

_TOOL_AT_TO_DX = {
    'meetingFolderTitle': 'meeting_folder_title',
    'functionalAdminEmail': 'functional_admin_email',
    'functionalAdminName': 'functional_admin_name',
    'restrictUsers': 'restrict_users',
    'unrestrictedUsers': 'unrestricted_users',
    'workingDays': 'working_days',
    'holidays': 'holidays',
    'delayUnavailableEndDays': 'delay_unavailable_end_days',
    'configGroups': 'config_groups',
    'deferParentReindex': 'defer_parent_reindex',
    'showExternalLinksSection': 'show_external_links_section',
    'advisersConfig': 'advisers_config',
}

_TOOL_DROPPED_FIELDS = {'enableScanDocs': False}


class ToolPloneMeeting(UniqueObject, OrderedFolder, BrowserDefaultMixin):
    """PloneMeeting portal tool -- singleton configuration manager."""

    security = ClassSecurityInfo()
    implements(interfaces.IToolPloneMeeting)

    meta_type = 'ToolPloneMeeting'
    portal_type = 'ToolPloneMeeting'

    ocrLanguages = ('eng', 'fra', 'deu', 'ita', 'nld', 'por', 'spa', 'vie')

    def __init__(self, id='portal_plonemeeting'):
        super(ToolPloneMeeting, self).__init__(id)
        self.meeting_folder_title = defValues.meetingFolderTitle
        self.functional_admin_email = defValues.functionalAdminEmail
        self.functional_admin_name = defValues.functionalAdminName
        self.restrict_users = defValues.restrictUsers
        self.unrestricted_users = defValues.unrestrictedUsers
        self.working_days = list(defValues.workingDays)
        self.holidays = list(defValues.holidays)
        self.delay_unavailable_end_days = list(defValues.delayUnavailableEndDays)
        self.config_groups = list(defValues.configGroups)
        self.defer_parent_reindex = list(defValues.deferParentReindex)
        self.show_external_links_section = list(defValues.showExternalLinksSection)
        self.advisers_config = list(defValues.advisersConfig)

    def __getattr__(self, name):
        if name.startswith('get') and name[3:4].isupper():
            field = name[3:]
            field = field[0].lower() + field[1:]
            if field in _TOOL_DROPPED_FIELDS:
                return lambda *a, **kw: _TOOL_DROPPED_FIELDS[field]
            dx_name = _TOOL_AT_TO_DX.get(field)
            if dx_name:
                return lambda *a, **kw: getattr(self, dx_name)
        if name.startswith('set') and name[3:4].isupper():
            field = name[3:]
            field = field[0].lower() + field[1:]
            dx_name = _TOOL_AT_TO_DX.get(field)
            if dx_name:
                custom_setter = '_set_' + dx_name
                if hasattr(type(self), custom_setter):
                    return getattr(self, custom_setter)
                def _generic_setter(v, _attr=dx_name, **kw):
                    if isinstance(v, (list, tuple)):
                        v = [dict(row) if isinstance(row, dict) else row
                             for row in v]
                    setattr(self, _attr, v)
                return _generic_setter
        if name in _TOOL_AT_TO_DX:
            return getattr(self, _TOOL_AT_TO_DX[name])
        return super(ToolPloneMeeting, self).__getattr__(name)

    def getField(self, name):
        return None

    # Names of advice workflow adaptations, ORDER IS IMPORTANT!
    advice_wf_adaptations = ()

    def indexObject(self):
        pass

    def reindexObject(self, idxs=None):
        pass

    def unindexObject(self):
        pass

    def invokeFactory(self, type_name, id, RESPONSE=None, *args, **kw):
        pt = api.portal.get_tool('portal_types')
        fti = pt.getTypeInfo(type_name)
        if fti is None:
            raise ValueError('Invalid type %s' % type_name)
        return fti.constructInstance(self, id, *args, **kw)

    def post_edit(self, is_created=False):
        self.configureAdvices()
        self.configureAutoConvert()
        self.adapted().onEdit(isCreated=is_created)

    def at_post_edit_script(self):
        self.post_edit(is_created=False)

    security.declarePrivate('at_post_create_script')

    def at_post_create_script(self):
        self.post_edit(is_created=True)

    def configureAdvices(self):
        """ """
        # Update MeetingAdvice portal_types if necessary
        self._updateMeetingAdvicePortalTypes()
        # Perform advice related workflow adaptations
        _performAdviceWorkflowAdaptations()
        # Finalize advice WF config with DX local roles
        self._finalizeAdviceWFConfig()

    def configureAutoConvert(self):
        """ """
        types_tool = api.portal.get_tool('portal_types')
        if self.auto_convert_annexes():
            # make sure annex/annexDecision portal_types use documentviewer
            # as default layout
            types_tool['annex'].default_view = "documentviewer"
            types_tool['annexDecision'].default_view = "documentviewer"
        else:
            # make sure annex/annexDecision portal_types use view as default view
            types_tool['annex'].default_view = "view"
            types_tool['annexDecision'].default_view = "view"

    def _updateMeetingAdvicePortalTypes(self):
        '''After Meeting/MeetingItem portal_types have been updated,
           update MeetingAdvice portal_types if necessary.
           This is the place to duplicate advice workflows
           to apply workflow adaptations on.'''
        # create a copy of each 'base_wf', we preprend the portal_type to create a new workflow
        for org_uids, adviser_infos in self.get_extra_adviser_infos(group_by_org_uids=True).items():
            portal_type = adviser_infos['portal_type']
            base_wf = adviser_infos['base_wf']
            advice_wf_id = '{0}__{1}'.format(portal_type, base_wf)
            duplicate_workflow(base_wf, advice_wf_id, portalTypeNames=[portal_type])

    def _finalizeAdviceWFConfig(self):
        """ """
        for org_uids, adviser_infos in self.get_extra_adviser_infos(group_by_org_uids=True).items():
            configure_advice_dx_localroles_for(
                adviser_infos['portal_type'], org_uids)

    security.declareProtected(ModifyPortalContent, '_set_config_groups')

    def _set_config_groups(self, value, **kwargs):
        '''Overrides the field 'configGroups' mutator to manage
           the 'row_id' column manually.  If empty, we need to add a
           unique id into it.'''
        for v in value:
            if v.get('orderindex_', None) == "template_row_marker":
                continue
            if not v.get('row_id', None):
                v['row_id'] = self.generateUniqueId()
        self.config_groups = list(value)

    security.declarePrivate('validate_holidays')

    def validate_holidays(self, values):
        '''Checks if encoded holidays are correct :
           - dates must respect format YYYY/MM/DD;
           - dates must be encoded ascending (older to newer);
           - a date in use (in computation of delay aware advice)
             can not be removed.'''
        if values == [{'date': '', 'orderindex_': 'template_row_marker'}]:
            return
        # first try to see if format is correct
        dates = []
        for row in values:
            if row.get('orderindex_', None) == 'template_row_marker':
                continue
            try:
                row_date = DateTime(row['date'])
                # and check if given format respect wished one
                if not row_date.strftime('%Y/%m/%d') == row['date']:
                    raise Exception
                year, month, day = row['date'].split('/')
                dates.append(datetime(int(year), int(month), int(day)))
            except Exception:
                return _('holidays_wrong_date_format_error')
        if dates:
            # now check that dates are encoded ascending
            previousDate = dates[0]
            for date in dates[1:]:
                if not date > previousDate:
                    return _('holidays_date_not_ascending_error')
                previousDate = date

        # check that if we removed a row, it was not in use
        dates_to_save = set([v['date'] for v in values if v['date']])
        stored_dates = set([v['date'] for v in self.holidays if v['date']])

        def _checkIfDateIsUsed(date, holidays, weekends, unavailable_weekdays):
            '''Check if the p_date we want to remove was in use.
               This returns an item_url if the date is already in use, nothing otherwise.'''
            # we are setting another field, it is not permitted if
            # the rule is in use, check every items if the rule is used
            catalog = api.portal.get_tool('portal_catalog')
            cfgs = self.objectValues('MeetingConfig')
            year, month, day = date.split('/')
            date_as_datetime = datetime(int(year), int(month), int(day))
            for cfg in cfgs:
                # compute the indexAdvisers depending on delay aware customAdvisers
                row_ids = [ca['row_id'] for ca in cfg.custom_advisers
                           if ca['delay']]
                indexAdvisers = [DELAYAWARE_ROW_ID_PATTERN.format(row_id)
                                 for row_id in row_ids]
                brains = catalog.unrestrictedSearchResults(
                    portal_type=cfg.getItemTypeName(),
                    indexAdvisers=indexAdvisers)
                for brain in brains:
                    item = brain.getObject()
                    for adviser in item.adviceIndex.values():
                        # if it is a delay aware advice, we check that the date
                        # was not used while computing delay
                        if adviser['delay'] and adviser['delay_started_on']:
                            start_date = adviser['delay_started_on']
                            if start_date > date_as_datetime:
                                continue
                            end_date = workday(start_date,
                                               int(adviser['delay']),
                                               holidays=holidays,
                                               weekends=weekends,
                                               unavailable_weekdays=unavailable_weekdays)
                            if end_date > date_as_datetime:
                                return item.absolute_url()

        removed_dates = stored_dates.difference(dates_to_save)
        holidays = self.get_holidays_as_datetime()
        weekends = self.get_non_working_day_numbers()
        unavailable_weekdays = self.get_unavailable_weekday_numbers()
        for date in removed_dates:
            an_item_url = _checkIfDateIsUsed(date, holidays, weekends, unavailable_weekdays)
            if an_item_url:
                return translate('holidays_removed_date_in_use_error',
                                 domain='PloneMeeting',
                                 mapping={'item_url': an_item_url, },
                                 context=self.REQUEST)

    def validate_configGroups(self, values):
        '''Checks if a removed configGroup was not in use.'''
        # check that if we removed a row, it was not in use by a MeetingConfig
        configGroups_to_save = set([v['row_id'] for v in values if v['row_id']])
        stored_configGroups = set([v['row_id'] for v in self.config_groups if v['row_id']])
        removed_configGroups = stored_configGroups.difference(configGroups_to_save)
        for configGroup in removed_configGroups:
            for cfg in self.objectValues('MeetingConfig'):
                if cfg.getConfigGroup() == configGroup:
                    config_group_title = [
                        v['label'] for v in self.config_groups if v['row_id'] == configGroup][0]
                    return translate(
                        'configGroup_removed_in_use_error',
                        domain='PloneMeeting',
                        mapping={'config_group_title': safe_unicode(config_group_title),
                                 'cfg_title': safe_unicode(cfg.Title()), },
                        context=self.REQUEST)

    def validate_advisersConfig(self, values):
        '''Validator for field advisersConfig.'''
        # remove the 'template_row_marker' value
        values = [v for v in values if not v.get('orderindex_') == 'template_row_marker']
        # a portal_type can only be selected one time
        portal_types = [v['portal_type'] for v in values]
        if len(portal_types) > len(set(portal_types)):
            return translate(
                'advisersConfig_several_portal_types_error',
                domain='PloneMeeting',
                context=self.REQUEST)
        # if some advice with portal_type exist, can not change
        # associated portal_type/base_wf
        to_save = set([(v['portal_type'], v['base_wf']) for v in values])
        stored = set([(v['portal_type'], v['base_wf']) for v in self.advisers_config])
        removed = stored.difference(to_save)
        added = to_save.difference(stored)
        catalog = api.portal.get_tool('portal_catalog')
        for portal_type, base_wf in tuple(removed) + tuple(added):
            brains = catalog(portal_type=portal_type)
            if brains:
                return translate(
                    'advisersConfig_portal_type_in_use_error',
                    domain='PloneMeeting',
                    mapping={'portal_type': safe_unicode(portal_type),
                             'advice_url': brains[0].getURL(), },
                    context=self.REQUEST)

    security.declarePublic('getActiveConfigs')

    def getActiveConfigs(self, check_using_groups=True, check_access=True):
        '''Gets the active meeting configurations.
           If check_using_groups is True, we check that current
           user is member of one of the cfg using_groups.'''
        res = []
        for cfg in self.objectValues('MeetingConfig'):
            if api.content.get_state(cfg) == 'active' and \
               (not check_access or
                (self.checkMayView(cfg) and
                    (self.isManager(cfg) or isPowerObserverForCfg(cfg) or
                        (check_using_groups and self.get_orgs_for_user(
                            using_groups=cfg.getUsingGroups()))))):
                res.append(cfg)
        return res

    security.declarePublic('get_plone_groups_for_user')

    def get_plone_groups_for_user(self, user_id=None, user=None, the_objects=False):
        """Redefined so it is available on tool in POD templates and TAL expressions."""
        logger.warn('ToolPloneMeeting.get_plone_groups_for_user is deprecated, '
                    'use imio.helpers.cache.get_plone_groups_for_user instead.')
        return get_plone_groups_for_user(user_id=user_id, user=user, the_objects=the_objects)

    def get_filtered_plone_groups_for_user(
            self, org_uids=[], user_id=None, suffixes=[], the_objects=False):
        """For caching reasons, we only use ram.cache on get_plone_groups_for_user
           to avoid too much entries when using p_org_uids.
           Use this when needing to filter on org_uids."""
        user_groups = get_plone_groups_for_user(
            user_id=user_id, the_objects=the_objects)
        if the_objects:
            user_groups = [plone_group for plone_group in user_groups
                           if (not org_uids or plone_group.id.split('_')[0] in org_uids) and
                           (not suffixes or '_' in plone_group.id and
                            plone_group.id.split('_')[1] in suffixes)]
        else:
            user_groups = [plone_group_id for plone_group_id in user_groups
                           if (not org_uids or plone_group_id.split('_')[0] in org_uids) and
                           (not suffixes or '_' in plone_group_id and
                            plone_group_id.split('_')[1] in suffixes)]
        return sorted(user_groups)

    def group_is_not_empty_cachekey(method, self, org_uid, suffix, user_id=None):
        '''cachekey method for self.group_is_not_empty.'''
        return (get_cachekey_volatile('_users_groups_value'),
                org_uid,
                suffix,
                user_id)

    # not ramcached see perf test
    # @ram.cache(group_is_not_empty_cachekey)
    def group_is_not_empty(self, org_uid, suffix, user_id=None):
        '''Is there any user in the group?
           Do not use ram.cache for this one, seems slower...'''
        portal = api.portal.get()
        plone_group_id = get_plone_group_id(org_uid, suffix)
        # for performance reasons, check directly in source_groups stored data
        group_users = portal.acl_users.source_groups._group_principal_map.get(plone_group_id, [])
        return len(group_users) and (not user_id or user_id in group_users)

    def _get_org_uids_for_user_cachekey(method,
                                        self,
                                        user_id=None,
                                        only_selected=True,
                                        suffixes=[],
                                        omitted_suffixes=[],
                                        using_groups=[]):
        '''cachekey method for self._get_orgs_for_user.'''
        return (get_cachekey_volatile('_users_groups_value'),
                (user_id or get_current_user_id(self.REQUEST)),
                only_selected, list(suffixes), list(omitted_suffixes), list(using_groups))

    security.declarePrivate('_get_org_uids_for_user')

    @ram.cache(_get_org_uids_for_user_cachekey)
    def _get_org_uids_for_user(self,
                               user_id=None,
                               only_selected=True,
                               suffixes=[],
                               omitted_suffixes=[],
                               using_groups=[]):
        '''This method is there to be cached as get_orgs_for_user(the_objects=True)
           will return objects, this may not be ram.cached.
           This submethod should not be called directly.'''
        res = []
        user_plone_group_ids = get_plone_groups_for_user(user_id)
        org_uids = get_organizations(only_selected=only_selected,
                                     kept_org_uids=using_groups,
                                     the_objects=False)
        for org_uid in org_uids:
            for suffix in get_all_suffixes(org_uid):
                if suffixes and (suffix not in suffixes):
                    continue
                if suffix in omitted_suffixes:
                    continue
                plone_group_id = get_plone_group_id(org_uid, suffix)
                if plone_group_id not in user_plone_group_ids:
                    continue
                # If we are here, the user belongs to this group.
                # Add the organization
                if org_uid not in res:
                    res.append(org_uid)
        return res

    def get_orgs_for_user(self,
                          user_id=None,
                          only_selected=True,
                          suffixes=[],
                          omitted_suffixes=[],
                          using_groups=[],
                          the_objects=False):
        '''Gets the organizations p_user_id belongs to. If p_user_id is None, we use the
           authenticated user. If p_only_selected is True, we consider only selected
           organizations. If p_suffixes is not empty, we select only orgs having
           at least one of p_suffixes. If p_omitted_suffixes, we do not consider
           orgs the user is in using those suffixes.
           If p_the_objects=True, organizations objects are returned, else the uids.'''
        res = self._get_org_uids_for_user(user_id=user_id,
                                          only_selected=only_selected,
                                          suffixes=suffixes,
                                          omitted_suffixes=omitted_suffixes,
                                          using_groups=using_groups)
        if res and the_objects:
            request = self.REQUEST
            # in some cases like in tests, request can not be retrieved
            key = "PloneMeeting-tool-get_orgs_for_user-{0}".format(
                '_'.join(sorted(res)))
            cache = IAnnotations(request)
            orgs = cache.get(key, None)

            if orgs is None:
                orgs = uuidsToObjects(res, ordered=True, unrestricted=True)
                logger.info(
                    "Getting organizations from "
                    "ToolPloneMeeting.get_orgs_for_user(the_objects=True)")
            cache[key] = list(orgs)
            res = orgs
        return res

    security.declarePublic('get_selectable_orgs')

    def get_selectable_orgs(self, cfg, only_selectable=True, user_id=None, the_objects=True):
        """
          Returns the selectable organizations for given p_user_id or currently connected user.
          If p_only_selectable is True, we will only return orgs for which current user is creator.
          If p_user_id is given, it will get orgs for which p_user_id is creator.
        """
        res = []
        if only_selectable:
            using_groups = cfg.getUsingGroups()
            res = self.get_orgs_for_user(
                user_id=user_id, suffixes=['creators', ],
                using_groups=using_groups,
                the_objects=the_objects)
        else:
            res = cfg.getUsingGroups(theObjects=the_objects)
        return res

    def userIsAmong_cachekey(method, self, suffixes, cfg=None, using_groups=[]):
        '''cachekey method for self.userIsAmong.'''
        return (get_cachekey_volatile('_users_groups_value'),
                get_current_user_id(self.REQUEST),
                suffixes,
                cfg and cfg.getId(),
                using_groups)

    security.declarePublic('userIsAmong')

    @ram.cache(userIsAmong_cachekey)
    def userIsAmong(self, suffixes, cfg=None, using_groups=[]):
        '''Check if the currently logged user is in at least one of p_suffixes-related Plone
           group.  p_suffixes is a list of suffixes.
           If cfg, we filter on cfg.usingGroups, if p_using_groups are given, we use it also.
           Parmater p_using_groups requires parameter p_cfg.'''
        res = False
        # display a warning if suffixes is not a tuple/list
        if not isinstance(suffixes, (tuple, list)):
            logger.warn("ToolPloneMeeting.userIsAmong parameter 'suffixes' must be "
                        "a tuple or list of suffixes, but we received '{0}'".format(suffixes))
        else:
            cfg_using_groups = cfg and cfg.getUsingGroups() or []
            if using_groups:
                using_groups = [using_group for using_group in using_groups
                                if not cfg_using_groups or using_group in cfg_using_groups]
            else:
                using_groups = cfg_using_groups
            activeOrgUids = [org_uid for org_uid in get_organizations(
                only_selected=True, the_objects=False, kept_org_uids=using_groups)]
            org_suffixes = get_all_suffixes()
            for plone_group_id in get_plone_groups_for_user():
                # check if the plone_group_id ends with a least one of the p_suffixes
                has_kept_suffixes = [suffix for suffix in suffixes
                                     if plone_group_id.endswith('_%s' % suffix)]
                if has_kept_suffixes:
                    org_uid, suffix = plone_group_id.split('_')
                    # if suffix is a org suffix and org is active, we are good
                    # if suffix is not an org suffix, it means it is something like _powerobservers
                    if (suffix in org_suffixes and org_uid in activeOrgUids) or \
                       suffix not in org_suffixes:
                        res = True
                        break
        return res

    def user_is_in_org(self,
                       org_id=None,
                       org_uid=None,
                       user_id=None,
                       only_selected=True,
                       suffixes=[],
                       omitted_suffixes=[],
                       using_groups=[]):
        """Check if user is member of one of the Plone groups linked
           to given p_org_id or p_org_uid.  Parameters are exclusive.
           p_org_id or p_org_uid can be a single value or a list of values.
           Other parameters from p_user_id=None to p_the_objects=True
           are default values passed to get_orgs_for_user."""
        if not org_id and not org_uid:
            return
        if not org_uid:
            # then we have an "org_id"
            if isinstance(org_id, str):
                org_id = [org_id]
            org_uid = [org_id_to_uid(_org_id) for _org_id in org_id]
        if isinstance(org_uid, str):
            org_uid = [org_uid]
        return bool(set(org_uid).intersection(self.get_orgs_for_user(
            user_id=user_id,
            only_selected=only_selected,
            suffixes=suffixes,
            omitted_suffixes=omitted_suffixes,
            using_groups=using_groups,
            the_objects=False)))

    security.declarePublic('getPloneMeetingFolder')

    def getPloneMeetingFolder(self, meetingConfigId, userId=None):
        '''Returns the folder, within the member area, that corresponds to
           p_meetingConfigId. If this folder and its parent folder ("My
           meetings" folder) do not exist, they are created.'''
        portal = api.portal.get_tool('portal_url').getPortalObject()
        home_folder = portal.portal_membership.getHomeFolder(userId)
        if home_folder is None:  # Necessary for the admin zope user
            return portal
        if not hasattr(aq_base(home_folder), ROOT_FOLDER):
            # Create the "My meetings" folder
            home_folder.invokeFactory('Folder', ROOT_FOLDER,
                                      title=self.meeting_folder_title)
            rootFolder = getattr(home_folder, ROOT_FOLDER)
            rootFolder.setConstrainTypesMode(1)
            rootFolder.setLocallyAllowedTypes(['Folder'])
            rootFolder.setImmediatelyAddableTypes(['Folder'])

        root_folder = getattr(home_folder, ROOT_FOLDER)
        if not hasattr(aq_base(root_folder), meetingConfigId):
            self.createMeetingConfigFolder(meetingConfigId, userId)
        return getattr(root_folder, meetingConfigId)

    security.declarePublic('createMeetingConfigFolder')

    def createMeetingConfigFolder(self, meetingConfigId, userId):
        '''Creates, within the "My meetings" folder, the sub-folder
           corresponding to p_meetingConfigId'''
        portal = api.portal.get_tool('portal_url').getPortalObject()
        root_folder = getattr(portal.portal_membership.getHomeFolder(userId),
                              ROOT_FOLDER)
        cfg = getattr(self, meetingConfigId)
        root_folder.invokeFactory('Folder', meetingConfigId,
                                  title=cfg.folder_title)
        mc_folder = getattr(root_folder, meetingConfigId)
        # We add the MEETING_CONFIG property to the folder
        mc_folder.manage_addProperty(MEETING_CONFIG, meetingConfigId, 'string')

        # manage faceted nav
        cfg._synchSearches(mc_folder)

        # constrain types
        mc_folder.setConstrainTypesMode(1)
        allowedTypes = [cfg.getItemTypeName(),
                        cfg.getMeetingTypeName()] + ['File', 'Folder']
        mc_folder.setLocallyAllowedTypes(allowedTypes)
        mc_folder.setImmediatelyAddableTypes([])
        # Define permissions on this folder. Some remarks:
        # * We override here default permissions/roles mappings as initially
        #   defined in config.py through calls to Products.CMFCore.permissions.
        #   setDefaultRoles (as generated by ArchGenXML). Indeed,
        #   setDefaultRoles may only specify the default Zope roles (Manager,
        #   Owner, Member) but we need to specify PloneMeeting-specific roles.
        # * By setting those permissions, we give "too much" permissions;
        #   security will be more constraining thanks to workflows linked to
        #   content types whose instances will be stored in this folder.
        # * The "write_permission" on field "MeetingItem.annexes" is set on
        #   "PloneMeeting: Add annex". It means that people having this
        #   permission may also disassociate annexes from items.
        mc_folder.manage_permission(ADD_CONTENT_PERMISSIONS['MeetingItem'],
                                    ('Owner', 'Manager', ), acquire=0)
        mc_folder.manage_permission(ADD_CONTENT_PERMISSIONS['Meeting'],
                                    ('MeetingManager', 'Manager', ), acquire=0)
        # Only Manager may change the set of allowable types in folders.
        mc_folder.manage_permission('Modify constrain types', ['Manager'], acquire=0)
        # Give MeetingManager localrole to relevant _meetingmanagers group
        mc_folder.manage_addLocalRoles("%s_%s" % (cfg.getId(), MEETINGMANAGERS_GROUP_SUFFIX), ('MeetingManager',))
        # clean cache for "plonemeeting.core.vocabularies.creatorsvocabulary"
        invalidate_cachekey_volatile_for("plonemeeting.core.vocabularies.creatorsvocabulary")
        invalidate_cachekey_volatile_for("plonemeeting.core.vocabularies.creatorsforfacetedfiltervocabulary")

    security.declarePublic('getMeetingConfig')

    def getMeetingConfig(self, context):
        '''Based on p_context's portal type, we get the corresponding meeting
           config.'''
        try:
            # Try DX-compatible attribute first (avoids conflict with DX schema field 'meeting_config')
            cfg_id = context.aq_acquire('_pm_mc_id')
        except AttributeError:
            try:
                cfg_id = context.aq_acquire(MEETING_CONFIG)
            except AttributeError:
                return None
        config = getattr(self, cfg_id, None)
        if config is not None:
            return config
        # During portal_factory creation the config is not yet stored in
        # portal_plonemeeting (cfg_id is a temporary portal_factory ID).
        # Traverse the acquisition chain from context to find the config directly.
        from plonemeeting.core.interfaces import IMeetingConfig as IMC
        obj = aq_inner(context)
        seen = set()
        while obj is not None:
            base_id = id(aq_base(obj))
            if base_id in seen:
                break
            seen.add(base_id)
            if IMC.providedBy(obj):
                return obj
            try:
                obj = aq_inner(obj).aq_parent
            except AttributeError:
                break
        return None

    security.declarePublic('getDefaultMeetingConfig')

    def getDefaultMeetingConfig(self):
        '''Gets the default meeting config.'''
        res = None
        activeConfigs = self.getActiveConfigs()
        for config in activeConfigs:
            if config.is_default:
                res = config
                break
        if not res and activeConfigs:
            return activeConfigs[0]
        return res

    def forJs(self, s):
        '''Returns p_s that can be inserted into a Javascript variable,
           without (double-)quotes problems.'''
        if not s:
            return ''
        res = s.replace('"', r'\"')
        res = res.replace("'", r"\'")
        res = res.replace('&nbsp;', ' ')
        return res

    security.declarePublic('checkMayView')

    def checkMayView(self, value):
        '''Check if we have the 'View' permission on p_value which can be an
           object or a brain. We use this because checkPermission('View',
           brain.getObject()) raises Unauthorized when the brain comes from
           the portal_catalog (not from the uid_catalog, because getObject()
           has been overridden in this tool and does an unrestrictedTraverse
           to the object.'''
        if hasattr(value, 'getPath'):
            obj = self.unrestrictedTraverse(value.getPath())
        else:
            obj = value
        return _checkPermission(View, obj)

    def isManager_cachekey(method, self, context=None, realManagers=False):
        '''cachekey method for self.isManager.'''
        # check also user id to avoid problems between Zope admin and anonymous
        # as they have both no group when initializing portal, some requests
        # (first time viewlet initialization?) have sometimes anonymous as user
        return (get_cachekey_volatile('_users_groups_value'),
                get_current_user_id(self.REQUEST),
                repr(context),
                realManagers)

    security.declarePublic('isManager')

    # not ramcached see perf test
    # @ram.cache(isManager_cachekey)
    def isManager(self, context=None, realManagers=False):
        '''Is the current user a 'MeetingManager' on context?  If p_realManagers is True,
           only returns True if user has role Manager/Site Administrator, either
           (by default) MeetingManager is also considered as a 'Manager'?'''
        if api.user.is_anonymous():
            return False

        if realManagers and context:
            raise Exception(
                "For caching reasons, please do not pass a \"context\" "
                "when calling \"tool.isManager\" with \"realManagers=True\"")
        elif not realManagers and context.__class__.__name__ != "MeetingConfig":
            raise Exception(
                "For caching reasons, please pass \"cfg\" as \"context\" "
                "when calling \"tool.isManager\" with \"realManagers=False\"")
        res = False
        if not realManagers:
            mmanager_group_id = get_plone_group_id(context.getId(), MEETINGMANAGERS_GROUP_SUFFIX)
            res = mmanager_group_id in get_plone_groups_for_user()
        if realManagers or not res:
            # can not use _checkPermission(ManagePortal, self)
            # because it would say True when using adopt_roles
            # use user.getRoles
            user = api.user.get_current()
            res = "Manager" in user.getRoles()
        return res

    def showPloneMeetingTab_cachekey(method, self, cfg):
        '''cachekey method for self.showPloneMeetingTab.'''
        if api.user.is_anonymous():
            return False
        # we only recompute if user groups changed or self changed
        return (cfg._p_mtime, get_plone_groups_for_user(), repr(cfg))

    @ram.cache(showPloneMeetingTab_cachekey)
    def showPloneMeetingTab(self, cfg):
        '''I show the PloneMeeting tabs (corresponding to meeting configs) if
           the user has one of the PloneMeeting roles and if the meeting config
           is active.'''
        # self.getActiveConfigs also check for 'View' access of current member to it
        if cfg not in self.getActiveConfigs():
            return False
        return True

    security.declarePublic('showAnnexesTab')

    def showAnnexesTab(self, context):
        '''Must we show the "Annexes" on given p_context ?'''
        if context.meta_type == 'MeetingItem' and \
           (context.isTemporary() or context.isDefinedInTool()):
            return False
        else:
            return True

    security.declarePrivate('listBooleanVocabulary')

    def listBooleanVocabulary(self):
        '''Vocabulary generating a boolean behaviour : just 2 values,
           one yes/True, and the other no/False.
           This is used in DataGridFields to avoid use of CheckBoxColumn
           that does not handle validation correctly.'''
        d = "PloneMeeting"
        res = DisplayList((
            ('0', translate('boolean_value_false', domain=d, context=self.REQUEST)),
            ('1', translate('boolean_value_true', domain=d, context=self.REQUEST)),
        ))
        return res

    security.declarePrivate('listWeekDays')

    def listWeekDays(self):
        '''Method returning list of week days used in vocabularies.'''
        res = DisplayList()
        for day in PY_DATETIME_WEEKDAYS:
            res.add(day,
                    translate('weekday_%s' % day,
                              domain='plonelocales',
                              context=self.REQUEST))
        return res

    security.declarePrivate('listDeferParentReindexes')

    def listDeferParentReindexes(self):
        '''Vocabulary for deferParentReindexes field.'''
        res = DisplayList()
        for defer in ('annex', 'item_reference'):
            res.add(defer,
                    translate('defer_reindex_for_%s' % defer,
                              domain='PloneMeeting',
                              context=self.REQUEST))
        return res

    def get_non_working_day_numbers_cachekey(method, self):
        '''cachekey method for self.get_non_working_day_numbers.'''
        # we only recompute if the tool was modified
        return (self.modified())

    security.declarePublic('get_non_working_day_numbers')

    @ram.cache(get_non_working_day_numbers_cachekey)
    def get_non_working_day_numbers(self):
        '''Return non working days, aka weekends.'''
        workingDays = self.working_days
        not_working_days = [day for day in PY_DATETIME_WEEKDAYS if day not in workingDays]
        return [PY_DATETIME_WEEKDAYS.index(not_working_day) for not_working_day in not_working_days]

    def get_holidays_as_datetime_cachekey(method, self):
        '''cachekey method for self.get_holidays_as_datetime.'''
        # we only recompute if the tool was modified
        return (self.modified())

    security.declarePublic('get_holidays_as_datetime')

    @ram.cache(get_holidays_as_datetime_cachekey)
    def get_holidays_as_datetime(self):
        '''Return the holidays but as datetime objects.'''
        res = []
        for row in self.holidays:
            year, month, day = row['date'].split('/')
            res.append(datetime(int(year), int(month), int(day)))
        return res

    def get_unavailable_weekday_numbers_cachekey(method, self):
        '''cachekey method for self.get_unavailable_weekday_numbers.'''
        # we only recompute if the tool was modified
        return (self.modified())

    security.declarePublic('get_unavailable_weekday_numbers')

    @ram.cache(get_unavailable_weekday_numbers_cachekey)
    def get_unavailable_weekday_numbers(self):
        '''Return unavailable days numbers from self.delay_unavailable_end_days.'''
        delayUnavailableEndDays = self.delay_unavailable_end_days
        unavailable_days = [day for day in PY_DATETIME_WEEKDAYS if day in delayUnavailableEndDays]
        return [PY_DATETIME_WEEKDAYS.index(unavailable_day) for unavailable_day in unavailable_days]

    security.declarePrivate('pasteItem')

    def pasteItem(self, destFolder, copiedData,
                  copyAnnexes=False, copyDecisionAnnexes=False,
                  newOwnerId=None, copyFields=DEFAULT_COPIED_FIELDS,
                  newPortalType=None, keepProposingGroup=False, keep_ftw_labels=False,
                  keptAnnexIds=[], keptDecisionAnnexIds=[],
                  ignoreUsingGroupsForMeetingManagers=True,
                  transfertAnnexWithScanIdTypes=[]):
        '''Paste objects (previously copied) in destFolder. If p_newOwnerId
           is specified, it will become the new owner of the item.
           This method does NOT manage after creation calls like at_post_create_script.
           If p_ignoreUsingGroupsForMeetingManagers=True and user is MeetingManager,
           then we will set check_using_groups=False while verifying if category
           is_selectable.'''
        # warn that we are pasting items
        # so it is not necessary to perform some methods
        # like updating advices as it will be removed here under
        self.REQUEST.set('currentlyPastingItems', True)
        destCfg = self.getMeetingConfig(destFolder)
        destCfgId = destCfg.getId()
        # Current user may not have the right to create object in destFolder.
        # We will grant him the right temporarily
        loggedUserId = get_current_user_id(self.REQUEST)
        userLocalRoles = destFolder.get_local_roles_for_userid(loggedUserId)
        destFolder.manage_addLocalRoles(loggedUserId, ('Owner',))

        # make sure 'update_all_categorized_elements' is not called while processing annexes
        self.REQUEST.set('defer_update_categorized_elements', True)
        self.REQUEST.set('defer_categorized_content_created_event', True)
        # store keptAnnexIds and keptDecisionAnnexIds in REQUEST
        # so it can be used by onItemCopied event so we optimize removal process
        self.REQUEST.set('pm_pasteItem_copyAnnexes', copyAnnexes)
        self.REQUEST.set('pm_pasteItem_copyDecisionAnnexes', copyDecisionAnnexes)
        self.REQUEST.set('pm_pasteItem_keptAnnexIds', keptAnnexIds)
        self.REQUEST.set('pm_pasteItem_keptDecisionAnnexIds', keptDecisionAnnexIds)
        # Perform the paste.
        # Temporarily bypass the legacy OFS meta_type check that fails for DX
        # content with a custom meta_type (not registered via AT registerType).
        # Replace with the DX-native FTI.isConstructionAllowed check.
        _orig_verify = destFolder.__class__._verifyObjectPaste

        def _dx_verifyObjectPaste(folder_self, obj, validate_src=1):
            from plone.dexterity.interfaces import IDexterityContent
            if IDexterityContent.providedBy(obj):
                from Products.CMFCore.interfaces import ITypeInformation
                from zope.component import queryUtility
                pt = getattr(aq_base(obj), 'portal_type', None)
                if pt:
                    fti = queryUtility(ITypeInformation, name=pt)
                    if fti is not None:
                        if not fti.isConstructionAllowed(folder_self):
                            raise Unauthorized
                        return
            _orig_verify(folder_self, obj, validate_src)
        destFolder.__class__._verifyObjectPaste = _dx_verifyObjectPaste
        try:
            pasteResult = destFolder.manage_pasteObjects(copiedData)
        finally:
            destFolder.__class__._verifyObjectPaste = _orig_verify
        # Restore the previous local roles for this user
        destFolder.manage_delLocalRoles([loggedUserId])
        if userLocalRoles:
            destFolder.manage_addLocalRoles(loggedUserId, userLocalRoles)
        # Now, we need to update information on every copied item.
        if not newOwnerId:
            # The new owner will become the currently logged user
            newOwnerId = loggedUserId
        wftool = api.portal.get_tool('portal_workflow')
        newItem = getattr(destFolder, pasteResult[0]['new_id'])
        # original item _at_rename_after_creation may have been changed
        newItem._at_rename_after_creation = MeetingItem._at_rename_after_creation
        # Get the copied item, we will need information from it
        copiedItem = None
        copiedId = CopySupport._cb_decode(copiedData)[1][0]
        m = OFS.Moniker.loadMoniker(copiedId)
        try:
            copiedItem = m.bind(destFolder.getPhysicalRoot())
        except ConflictError:
            raise
        except Exception:
            raise PloneMeetingError('Could not copy.')

        isManager = self.isManager(destCfg)
        originCfg = self.getMeetingConfig(copiedItem)

        # Let the logged user do everything on the newly created item
        with api.env.adopt_roles(['Manager']):
            newItem.setCreators((newOwnerId,))
            # The creation date is kept, redefine it
            newItem.setCreationDate(DateTime())

            # Change the new item portal_type dynamically (wooow) if needed
            if newPortalType:
                newItem.portal_type = newPortalType
                # Rename the workflow used in workflow_history because the used workflow
                # has changed (more than probably)
                oldWFName = wftool.getWorkflowsFor(copiedItem)[0].id
                newWFName = wftool.getWorkflowsFor(newItem)[0].id
                oldHistory = newItem.workflow_history
                tmpDict = PersistentMapping({newWFName: oldHistory[oldWFName]})
                # make sure current review_state is right, in case initial_state
                # of newPortalType WF is not the same as original portal_type WF, correct this
                newItemWF = wftool.getWorkflowsFor(newItem)[0]
                if tmpDict[newWFName][0]['review_state'] != newItemWF.initial_state:
                    # in this case, the current wf state is wrong, we will correct it
                    tmpDict[newWFName][0]['review_state'] = newItemWF.initial_state
                newItem.workflow_history = tmpDict
                # update security settings of new item as workflow permissions could have changed...
                newItemWF.updateRoleMappingsFor(newItem)

            # manage ftw.labels
            annotations = IAnnotations(newItem)
            if not keep_ftw_labels and FTW_LABELS_ANNOTATION_KEY in annotations:
                del annotations[FTW_LABELS_ANNOTATION_KEY]

            # Set fields not in the copyFields list to their default value
            # 'id' and 'proposing_group' will be kept in anyway
            fieldsToKeep = ['id', 'proposing_group'] + copyFields
            # remove 'category' from fieldsToKeep if it is disabled
            if 'category' in fieldsToKeep:
                category = copiedItem.getCategory(theObject=True)
                if category and not category.is_selectable(
                        userId=loggedUserId, ignore_using_groups=isManager):
                    fieldsToKeep.remove('category')
            # remove 'classifier' from fieldsToKeep if it is disabled
            if 'classifier' in fieldsToKeep:
                classifier = copiedItem.getClassifier(theObject=True)
                if classifier and not classifier.is_selectable(
                        userId=loggedUserId, ignore_using_groups=isManager):
                    fieldsToKeep.remove('classifier')

            newItem._at_creation_flag = True
            from plonemeeting.core.content.meetingitem import IMeetingItem
            fieldsToKeepSet = set(fieldsToKeep)
            fieldsToKeepSet.add('id')
            for field_name, field in IMeetingItem.namesAndDescriptions():
                if field_name in fieldsToKeepSet:
                    continue
                setattr(newItem, field_name, field.default)
            if 'preferred_meeting_path' not in fieldsToKeep:
                newItem.preferred_meeting_path = None
            newItem._at_creation_flag = False

            if newPortalType:
                # manage categories mapping, if original and new items use
                # categories, we check if a mapping is defined in the configuration of the original item
                originalCategory = copiedItem.getCategory(theObject=True)
                if originalCategory and "category" in destCfg.used_item_attributes:
                    # find out if something is defined when sending an item to destMeetingConfig
                    for destCat in originalCategory.category_mapping_when_cloning_to_other_mc:
                        if destCat.split('.')[0] == destCfgId:
                            # we found a mapping defined for the new category, apply it
                            # get the category so it fails if it does not exist (that should not be possible...)
                            newCat = getattr(destCfg.categories, destCat.split('.')[1])
                            newItem.category = newCat.getId()
                            break

            # Set some default values that could not be initialized properly
            if 'to_discuss' in copyFields and destCfg.to_discuss_set_on_item_insert:
                toDiscussDefault = destCfg.to_discuss_default
                newItem.to_discuss = toDiscussDefault

            # if we have left annexes, we manage it
            plone_utils = api.portal.get_tool('plone_utils')
            annexes = get_annexes(newItem)
            if annexes:
                oldAnnexes = get_annexes(copiedItem)
                for oldAnnex in oldAnnexes:
                    newAnnex = newItem.get(oldAnnex.getId())
                    if not newAnnex:
                        # this annex was removed by another event
                        continue
                    # In case the item is copied from another MeetingConfig, we need
                    # to update every annex.content_category because it still refers
                    # the annexType in the old MeetingConfig the item is copied from
                    if newPortalType:
                        # manage the otherMCCorrespondence
                        new_annex_category = self._updateContentCategoryAfterSentToOtherMeetingConfig(
                            newAnnex, originCfg, destCfgId)
                        if new_annex_category is None:
                            msg = translate('annex_not_kept_item_paste_info',
                                            mapping={'annexTitle': safe_unicode(newAnnex.Title())},
                                            domain='PloneMeeting',
                                            context=self.REQUEST)
                            plone_utils.addPortalMessage(msg, 'info')
                            unrestrictedRemoveGivenObject(newAnnex)
                            continue
                        elif new_annex_category.only_pdf and \
                                newAnnex.file.contentType != 'application/pdf':
                            msg = translate('annex_not_kept_because_only_pdf_annex_type_warning',
                                            mapping={'annexTitle': safe_unicode(newAnnex.Title())},
                                            domain='PloneMeeting',
                                            context=self.REQUEST)
                            plone_utils.addPortalMessage(msg, 'warning')
                            unrestrictedRemoveGivenObject(newAnnex)
                            continue

                    # if not newPortalType, annex with a scan_id is deleted
                    # if annex portal_type not defined in transfertAnnexWithScanIdTypes
                    # if newPortalType, it is managed here above by
                    # _updateContentCategoryAfterSentToOtherMeetingConfig
                    # annex is removed we do not reach this point
                    if newAnnex.portal_type in transfertAnnexWithScanIdTypes and \
                       getattr(oldAnnex, 'scan_id', None):
                        # transfer annex scan_id, it was copied to newAnnex, do not touch
                        # but we remove it from oldAnnex and we reindex
                        oldAnnex.scan_id = None
                        oldAnnex.reindexObject(idxs=['scan_id'])
                        # reindex parent because SearchableText still contains the annex scan_id
                        reindex_object(copiedItem, update_metadata=False, mark_to_reindex=True)
                    elif getattr(newAnnex, 'scan_id', None):
                        msg = translate('annex_not_kept_because_using_scan_id',
                                        mapping={'annexTitle': safe_unicode(newAnnex.Title())},
                                        domain='PloneMeeting',
                                        context=newItem.REQUEST)
                        plone_utils.addPortalMessage(msg, type='warning')
                        unrestrictedRemoveGivenObject(newAnnex)
                        continue
                    # remove annexes that are not downloadable
                    if not oldAnnex.show_download():
                        msg = translate('annex_show_preview_not_kept',
                                        mapping={'annexTitle': safe_unicode(oldAnnex.Title())},
                                        domain='PloneMeeting',
                                        context=self.REQUEST)
                        plone_utils.addPortalMessage(msg, 'info')
                        unrestrictedRemoveGivenObject(newAnnex)

                    # initialize to_print correctly regarding configuration
                    if not destCfg.keep_original_to_print_of_cloned_items:
                        newAnnex.to_print = \
                            get_category_object(newAnnex, newAnnex.content_category).to_print

            # Change the proposing group if the item owner does not belong to
            # the defined proposing group, except if p_keepProposingGroup is True
            if not keepProposingGroup:
                # use a primary_organization if possible
                person = get_person_from_userid(get_current_user_id())
                primary_org = person.primary_organization if person else None
                # proposingGroupWithGroupInCharge
                if newItem.attribute_is_used('proposingGroupWithGroupInCharge'):
                    vocab = get_vocab(
                        newItem,
                        u'plonemeeting.core.vocabularies.userproposinggroupswithgroupsinchargevocabulary',
                        only_factory=True)
                    userProposingGroupTerms = vocab(newItem, include_stored=False)._terms
                    if userProposingGroupTerms:
                        token = userProposingGroupTerms[0].token
                        if primary_org:
                            tokens = [term.token for term in userProposingGroupTerms
                                      if term.token.startswith(primary_org)]
                            token = tokens[0] if tokens else token
                        newItem.setProposingGroupWithGroupInCharge(token)
                else:
                    # proposingGroup
                    vocab = get_vocab(
                        newItem,
                        u'plonemeeting.core.vocabularies.userproposinggroupsvocabulary',
                        include_stored=False)
                    if vocab._terms:
                        token = vocab._terms[0].token
                        if primary_org:
                            try:
                                token = vocab.getTermByToken(primary_org).token
                            except LookupError:
                                pass
                        newItem.proposing_group = token

            if newOwnerId != loggedUserId:
                plone_utils.changeOwnershipOf(newItem, newOwnerId)

            # update annex index after every user/groups things are setup
            # because annexes confidentiality relies on all this
            update_all_categorized_elements(newItem)
            # remove defered call to 'update_all_categorized_elements'
            self.REQUEST.set('defer_update_categorized_elements', False)
            self.REQUEST.set('defer_categorized_content_created_event', False)

            # The copy/paste has transferred history. We must clean the history
            # of the cloned object then add the 'Creation' event.
            wfName = wftool.getWorkflowsFor(newItem)[0].id
            newItem.workflow_history[wfName] = ()
            add_event_to_wf_history(newItem,
                                    action=None,
                                    actor=newOwnerId or newItem.Creator(),
                                    comments=None)

            # The copy/paste has transferred annotations,
            # remove ones related to item sent to other MC
            anns_to_remove = [ann for ann in annotations
                              if ann.startswith(SENT_TO_OTHER_MC_ANNOTATION_BASE_KEY)]
            for ann_to_remove in anns_to_remove:
                del annotations[ann_to_remove]

            self.REQUEST.set('currentlyPastingItems', False)
        return newItem

    def _updateContentCategoryAfterSentToOtherMeetingConfig(self, annex, originCfg, destCfgId):
        '''
          Update the content_category of the annex while an item is sent from
          a MeetingConfig to another : find a corresponding content_category in the new MeetingConfig :
          - either we have a correspondence defined on the original ContentCategory specifying what is the
            ContentCategory to use in the new MeetingConfig;
          - or if we can not get a correspondence, we use the default ContentCategory of the new MeetingConfig.
          Moreover it takes care of setting a correct portal_type in case we are changing from annex to annexDecision.
          Returns True if the content_category was actually updated, False if no correspondence could be found.
        '''
        catalog = api.portal.get_tool('portal_catalog')
        if annex.portal_type == 'annexDecision':
            self.REQUEST.set('force_use_item_decision_annexes_group', True)
            annex_category = get_category_object(originCfg, annex.content_category)
            self.REQUEST.set('force_use_item_decision_annexes_group', False)
        else:
            annex_category = get_category_object(originCfg, annex.content_category)

        # special case when annex not kept
        annex_not_kept = ANNEX_NOT_KEPT.format(destCfgId)
        if annex_category.other_mc_correspondences is not None and \
           annex_not_kept in annex_category.other_mc_correspondences:
            return None

        other_mc_correspondences = []
        if annex_category.other_mc_correspondences:
            annex_cfg_id = self.getMeetingConfig(annex).getId()
            other_mc_correspondences = [
                brain._unrestrictedGetObject() for brain in catalog.unrestrictedSearchResults(
                    UID=tuple(annex_category.other_mc_correspondences),
                    enabled=True)
                if "/portal_plonemeeting/{0}".format(annex_cfg_id) in brain.getPath()]

        # special case when annex has a scan_id, a correspondence must have been defined
        if getattr(annex, 'scan_id', None):
            if not other_mc_correspondences:
                # this will remove the annex
                return None
            annex.scan_id = None
            annex.reindexObject(idxs=['scan_id'])

        if other_mc_correspondences:
            other_mc_correspondence = other_mc_correspondences[0]
            adapted_annex = IconifiedCategorization(annex)
            setattr(adapted_annex,
                    'content_category',
                    calculate_category_id(other_mc_correspondence))
        else:
            # use default category
            categories = get_categories(annex, sort_on='getObjPositionInParent')
            if not categories:
                return None
            else:
                adapted_annex = IconifiedCategorization(annex)
                setattr(adapted_annex,
                        'content_category',
                        calculate_category_id(categories[0].getObject()))
        # try to get the category, if it raises KeyError it means we need to change the annex portal_type
        try:
            new_annex_category = get_category_object(annex, annex.content_category)
        except KeyError:
            if annex.portal_type == 'annex':
                annex.portal_type = 'annexDecision'
            else:
                annex.portal_type = 'annex'
            # reindexObject without idxs would update modified
            reindex_object(annex, no_idxs=['SearchableText'])
            # now it should not fail anymore
            new_annex_category = get_category_object(annex, annex.content_category)

        return new_annex_category

    security.declarePublic('getSelf')

    def getSelf(self):
        if self.meta_type != 'ToolPloneMeeting':
            return self.context
        return self

    security.declarePublic('adapted')

    def adapted(self):
        return getCustomAdapter(self)

    security.declareProtected(ModifyPortalContent, 'onEdit')

    def onEdit(self, isCreated):
        '''See doc in interfaces.py.'''
        pass

    security.declarePublic('format_date')

    def format_date(self, date, lang=None, short=False,
                    with_hour=False, prefixed=False, prefix="meeting_of",
                    with_week_day_name=False):
        '''Returns p_meeting.date formatted.
           - If p_lang is specified, it translates translatable elements (if
             any), like day of week or month, in p_lang. Else, it translates it
             in the user language (see tool.getUserLanguage).
           - if p_short is True, is uses a special, shortened, format (ie, day
             of month is replaced with a number)
           - If p_prefix is True, the translated prefix is
             prepended to the result.'''
        # Get the format for the rendering of p_aDate
        if short:
            fmt = '%d/%m/%Y'
        else:
            fmt = '%d %mt %Y'
        if with_week_day_name:
            fmt = fmt.replace('%d', '%A %d')
            weekday = translate('weekday_%s' % PY_DATETIME_WEEKDAYS[date.weekday()],
                                target_language=lang,
                                domain='plonelocales',
                                context=self.REQUEST)
            fmt = fmt.replace('%A', weekday)
        if with_hour and (date.hour or date.minute):
            fmt += ' (%H:%M)'
        # Apply p_fmt to p_aDate. Manage first special symbols corresponding to
        # translated names of days and months.
        # Manage day of week
        if not lang:
            lang = api.portal.get_tool('portal_languages').getDefaultLanguage()

        # Manage month
        month = translate(monthsIds[date.month], target_language=lang,
                          domain='plonelocales', context=self.REQUEST)
        fmt = fmt.replace('%mt', month.lower())
        fmt = fmt.replace('%MT', month)
        # Resolve all other, standard, symbols
        # fmt can not be unicode
        if isinstance(fmt, six.text_type):
            fmt = fmt.encode('utf-8')
        res = safe_unicode(date.strftime(fmt))
        # Finally, prefix the date with p_prefix when required
        if prefixed:
            res = u"{0} {1}".format(
                translate(prefix,
                          domain='PloneMeeting',
                          context=self.REQUEST),
                res)
        return res

    security.declareProtected(ModifyPortalContent, 'convertAnnexes')

    def convertAnnexes(self):
        '''Convert all annexes using collective.documentviewer.'''
        if not self.isManager(realManagers=True):
            raise Unauthorized

        catalog = api.portal.get_tool('portal_catalog')
        # update annexes in items and advices
        brains = catalog.unrestrictedSearchResults(meta_type='MeetingItem') + \
            catalog.unrestrictedSearchResults(
                object_provides='plonemeeting.core.content.advice.IMeetingAdvice')
        for brain in brains:
            obj = brain.getObject()
            annexes = get_categorized_elements(obj, result_type='objects')
            cfg = self.getMeetingConfig(obj)
            for annex in annexes:
                to_be_printed_activated = get_config_root(annex)
                # convert if auto_convert is enabled or to_print is enabled for printing
                if (self.auto_convert_annexes() or
                    (to_be_printed_activated and cfg.annex_to_print_mode == 'enabled_for_printing')) and \
                   not IIconifiedPreview(annex).converted:
                    # P6 migration: zc.async dropped, convert inline. Reimplement async in Stage D.
                    # queueJob(annex)
                    Converter(annex)()
        api.portal.show_message('Done.', request=self.REQUEST)
        return self.REQUEST.RESPONSE.redirect(self.REQUEST['HTTP_REFERER'])

    def _removeAnnexPreviewFor(self, parent, annex):
        '''Remove annex collective.documentviewer preview.'''
        remove_generated_previews(annex)
        annex_infos = parent.categorized_elements.get(annex.UID())
        if annex_infos:
            annex_infos['preview_status'] = IIconifiedPreview(annex).status
        parent._p_changed = True

    security.declareProtected(ModifyPortalContent, 'removeAnnexesPreviews')

    def removeAnnexesPreviews(self, query={}):
        '''Remove every annexes previews of items presented to closed meetings.'''
        if not self.isManager(realManagers=True):
            raise Unauthorized

        if not query:
            query = {'object_provides': IMeeting.__identifier__,
                     'review_state': Meeting.MEETINGCLOSEDSTATES,
                     'sort_on': 'meeting_date'}
        catalog = api.portal.get_tool('portal_catalog')
        # remove annexes previews of items of closed Meetings
        brains = catalog.unrestrictedSearchResults(**query)
        numberOfBrains = len(brains)
        i = 1
        for brain in brains:
            meeting = brain.getObject()
            logger.info('%d/%d Removing annexes of items of meeting %s at %s' %
                        (i,
                         numberOfBrains,
                         brain.portal_type,
                         '/'.join(meeting.getPhysicalPath())))
            i = i + 1
            for item in meeting.get_items(ordered=True):
                annexes = get_annexes(item)
                for annex in annexes:
                    self._removeAnnexPreviewFor(item, annex)
                extras = 'item={0} number_of_annexes={1}'.format(repr(item), len(annexes))
                fplog('remove_annex_previews', extras=extras)

        logger.info('Done.')
        api.portal.show_message('Done.', request=self.REQUEST)
        return self.REQUEST.RESPONSE.redirect(self.REQUEST['HTTP_REFERER'])

    def auto_convert_annexes(self):
        """Return True if auto_convert is enabled in the c.documentviewer settings."""
        portal = api.portal.get()
        gsettings = GlobalSettings(portal)
        return gsettings.auto_convert

    def hasAnnexes(self, context, portal_type='annex'):
        '''Does given p_context contains annexes of type p_portal_type?'''
        return bool(get_categorized_elements(context, portal_type=portal_type))

    security.declareProtected(ModifyPortalContent, 'update_all_local_roles')

    def update_all_local_roles(self,
                               meta_type=('Meeting', 'MeetingItem'),
                               portal_type=(),
                               brains=[],
                               log=True,
                               redirect=True,
                               **kw):
        '''Update local_roles on Meeting and MeetingItem,
           this is used to reflect configuration changes regarding access.
           If p_brains is given, we use it, else we get brains using
           p_meta_type and p_portal_type.'''
        startTime = time.time()
        if not brains:
            catalog = api.portal.get_tool('portal_catalog')
            # meta_type does not work in DX, use object_provides
            query = {'object_provides': []}
            if 'Meeting' in meta_type:
                query['object_provides'].append(IMeeting.__identifier__)
            if 'MeetingItem' in meta_type:
                query['object_provides'].append(IMeetingItem.__identifier__)
            if portal_type:
                query['portal_type'] = portal_type
            query.update(kw)
            brains = catalog.unrestrictedSearchResults(**query)
        numberOfBrains = len(brains)
        i = 1
        warnings = []
        if log:
            extras = 'number_of_elements={0}'.format(numberOfBrains)
            fplog('update_all_localroles', extras=extras)

        pghandler = ZLogHandler(steps=1000)
        pghandler.init('Updating local roles...', len(brains))
        for brain in brains:
            try:
                itemOrMeeting = brain.getObject()
            except AttributeError:
                warning = 'Could not getObject() element at %s' % brain.getPath()
                warnings.append(warning)
                logger.warn(warning)
                continue

            pghandler.report(i)
            i = i + 1
            itemOrMeeting.update_local_roles(avoid_reindex=True)

        pghandler.finish()
        logger.info(end_time(
            startTime,
            base_msg="update_all_local_roles finished in ",
            total_number=numberOfBrains))
        if redirect:
            api.portal.show_message('Done.', request=self.REQUEST)
            return self.REQUEST.RESPONSE.redirect(self.REQUEST['HTTP_REFERER'])
        else:
            return warnings

    security.declareProtected(ModifyPortalContent, 'doInvalidateAllCache')

    def doInvalidateAllCache(self):
        """Form action that will invalidate the cache."""
        self.invalidateAllCache()
        api.portal.show_message(_('All cache was invalidated'), request=self.REQUEST)
        return self.REQUEST.RESPONSE.redirect(self.REQUEST['HTTP_REFERER'])

    security.declareProtected(ModifyPortalContent, 'invalidateAllCache')

    def invalidateAllCache(self):
        """Invalidate RAM cache and just notifyModified so etag toolmodified invalidate all brower cache."""
        cleanRamCache()
        cleanVocabularyCacheFor()
        cleanForeverCache()
        self._p_changed = True
        logger.info('All cache was invalidated.')

    security.declarePublic('deleteHistoryEvent')

    def deleteHistoryEvent(self, obj, eventToDelete):
        '''Deletes an p_event in p_obj's history.'''
        history = []
        eventToDelete = DateTime(eventToDelete)
        wfTool = api.portal.get_tool('portal_workflow')
        workflow_name = wfTool.getWorkflowsFor(obj)[0].getId()
        for event in obj.workflow_history[workflow_name]:
            # Allow to remove data changes only.
            if (event['action'] != '_datachange_') or \
               (event['time'] != eventToDelete):
                history.append(event)
        obj.workflow_history[workflow_name] = tuple(history)

    def showHolidaysWarning(self, cfg):
        """Condition for showing the 'holidays_waring_message'."""
        if cfg is not None and cfg.__class__.__name__ == "MeetingConfig":
            holidays = self.holidays
            # if user isManager and last defined holiday is in less than 60 days, display warning
            if self.isManager(cfg) and \
               (not holidays or DateTime(holidays[-1]['date']) < DateTime() + 60):
                return True
        return False

    def performCustomWFAdaptations(self,
                                   meetingConfig,
                                   wfAdaptation,
                                   logger,
                                   itemWorkflow,
                                   meetingWorkflow):
        '''See doc in interfaces.py.'''
        return False

    def performCustomAdviceWFAdaptations(self,
                                         meetingConfig,
                                         wfAdaptation,
                                         logger,
                                         advice_wf_id):
        '''See doc in interfaces.py.'''
        return False

    def get_extra_adviser_infos(self, group_by_org_uids=False):
        '''Helper to get ToolPloneMeeting.advisersConfig's data.
        This will return a dict with following informations:
           - key: an adviser organization uid, or a list of org uids when
             p_group_by_org_uids=True
           - value : a dict with:
               - 'portal_type': the portal_type to use to give the advice;
               - 'base_wf': the name of the base WF used by this portal_type;
                 will be used to generate a patched_ prefixed WF to apply WFAdaptations on;
               - 'wf_adaptations': a list of workflow adaptations to apply.
        '''
        res = {}
        for row in self.advisers_config:
            if group_by_org_uids:
                res[tuple(row['org_uids'])] = {
                    k: v for k, v in row.items() if k != 'org_uids'}
            else:
                for org_uid in row['org_uids']:
                    # append every existing values
                    res[org_uid] = {
                        k: v for k, v in row.items() if k != 'org_uids'}
        return res

    def extraAdviceTypes(self):
        '''See doc in interfaces.py.'''
        return []

    def _advicePortalTypeForAdviser(self, org_uid):
        """Advices may use several 'meetingadvice' portal_types.  A portal_type is associated to
           an adviser org_uid, this method will return the advice portal_type used by given p_org_uid."""
        adviser_infos = self.get_extra_adviser_infos().get(org_uid, {})
        advice_portal_type = adviser_infos.get('portal_type', None)
        return advice_portal_type or 'meetingadvice'

    def getGroupedConfigs_cachekey(method, self, config_group=None, check_access=True, as_items=False):
        '''cachekey method for self.getGroupedConfigs.'''
        if api.user.is_anonymous():
            return False

        # we only recompute if cfgs, user groups or params changed
        cfg_infos = [(cfg._p_mtime, cfg.id) for cfg in self.objectValues('MeetingConfig')]
        return (self.modified(), cfg_infos, get_plone_groups_for_user(), config_group, check_access, as_items)

    security.declarePublic('getGroupedConfigs')

    @ram.cache(getGroupedConfigs_cachekey)
    def getGroupedConfigs(self, config_group=None, check_access=True, as_items=False):
        """Return an OrderedDict with configGroup row_id/label tuple as key
           and list of MeetingConfigs as value."""
        data = OrderedDict()
        if not api.user.is_anonymous():
            configGroups = list(self.config_groups)
            configGroups.append(
                {'row_id': '',
                 'label': translate('_no_config_group_',
                                    domain='PloneMeeting',
                                    context=self.REQUEST,
                                    default='Not grouped meeting configurations'),
                 'full_label': u''})
            for configGroup in configGroups:
                if config_group and configGroup['row_id'] != config_group:
                    continue
                res = []
                for cfg in self.objectValues('MeetingConfig'):
                    if check_access and not self.showPloneMeetingTab(cfg):
                        continue
                    if cfg.getConfigGroup() == configGroup['row_id']:
                        res.append({'id': cfg.getId(),
                                    'title': cfg.Title()})
                data[(configGroup['row_id'], configGroup['label'], configGroup['full_label'])] = res

        if as_items:
            return list(data.items())
        else:
            return data

    security.declarePublic('is_zope_admin')

    def is_zope_admin(self):
        '''Is current user a Zope admin?'''
        return check_zope_admin()


InitializeClass(ToolPloneMeeting)
