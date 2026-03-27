# -*- coding: utf-8 -*-

from imio.esign.browser.settings import IImioEsignSettings
from plone import api
from plone.registry.interfaces import IRecordModifiedEvent


def onRegistryModified(event):
    """
        Manage our record changes for imio.esign
    """
    if IRecordModifiedEvent.providedBy(event) and \
       event.record.interfaceName and \
       event.record.interface == IImioEsignSettings and \
       event.record.fieldName == 'enabled':
        # clear cache, essentially to show the "Parapheo" tab
        tool = api.portal.get_tool('portal_plonemeeting')
        tool.invalidateAllCache()
        # show/hide relevant actions depending on "enabled"
        portal_actions = api.portal.get_tool('portal_actions')
        enabled = event.newValue
        portal_actions.object_buttons.remove_from_esign_session.visible = enabled
        portal_actions.object_buttons.remove_item_from_esign_session.visible = enabled
        portal_actions.portal_tabs.parapheo.visible = enabled
