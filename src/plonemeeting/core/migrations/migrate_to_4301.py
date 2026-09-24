# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from plone.base.utils import get_installer
from plonemeeting.core.migrations import logger
from plonemeeting.core.migrations import Migrator


# Packages that ship their scripts and styles as Plone 6 bundle records.
BUNDLE_PRODUCTS = (
    'plonemeeting.core',
    'imio.actionspanel',
    'ftw.labels',
    'imio.annex',
    'imio.dashboard',
    'collective.js.iframeresizer',
    'collective.eeafaceted.collectionwidget',
    'collective.eeafaceted.dashboard',
    'collective.z3cform.select2',
)

# Skin layers that no longer exist: the Plone 4 theme layers and the
# PloneMeeting styles layer, replaced by the browser/static resources.
OBSOLETE_SKIN_LAYERS = (
    'plonemeetingskin_styles',
    'plonemeetingskin_images',
    'imioapps_styles',
    'imioapps_images',
    'plonemeeting_styles',
)


class Migrate_To_4301(Migrator):

    def _installQuickupload(self):
        """Install collective.quickupload, the multi-upload widget of imio.annex.
           Sites created before imio.annex declared it as a profile dependency
           do not have it."""
        logger.info('Installing collective.quickupload...')
        installer = get_installer(self.portal, self.request)
        if not installer.is_product_installed('collective.quickupload'):
            installer.install_product('collective.quickupload')
        logger.info('Installing collective.quickupload... Done.')

    def _loadFrontEndBundles(self):
        """Load the bundle records of PloneMeeting and of the dependencies
           that only had Plone 4 resource registries.
           Then remove the bundle records that point to missing resources."""
        logger.info('Loading front-end bundles...')
        for product in BUNDLE_PRODUCTS:
            self.runProfileSteps(product, steps=['plone.app.registry'])
        self.cleanRegistries(registries=('bundles_registry', ))
        logger.info('Loading front-end bundles... Done.')

    def _removeObsoleteSkinLayers(self):
        """Remove the portal_skins layers that no longer exist."""
        logger.info('Removing obsolete skin layers...')
        skins = self.portal.portal_skins
        to_remove = [layer_id for layer_id in OBSOLETE_SKIN_LAYERS
                     if layer_id in skins.objectIds()]
        if to_remove:
            skins.manage_delObjects(to_remove)
        for skin_name, path in skins.getSkinPaths():
            layers = [layer.strip() for layer in path.split(',')
                      if layer.strip() not in OBSOLETE_SKIN_LAYERS]
            skins.addSkinSelection(skin_name, ','.join(layers))
        logger.info('Removing obsolete skin layers... Done.')

    def run(self, extra_omitted=[], from_migration_to_4200=False):
        logger.info('Migrating to PloneMeeting 4301...')
        self._installQuickupload()
        self._loadFrontEndBundles()
        self._removeObsoleteSkinLayers()
        logger.info('Migrating to PloneMeeting 4301... Done.')


def migrate(context):
    '''This migration function will:

       1) Install collective.quickupload.
       2) Load the Plone 6 bundle records of PloneMeeting and its dependencies.
       3) Remove the portal_skins layers that no longer exist.
    '''
    migrator = Migrate_To_4301(context)
    migrator.run()
    migrator.finish()
