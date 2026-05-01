# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from imio.helpers.setup import load_type_from_package
from Products.PloneMeeting.migrations import logger
from Products.PloneMeeting.migrations import Migrator
from Products.PloneMeeting.ToolPloneMeeting import _TOOL_AT_TO_DX


_AT_ARTIFACTS = (
    '_at_rename_after_creation',
    'schema',
    '_signature',
    'at_references',
)


class Migrate_To_4300(Migrator):

    def _migrateMeetingConfigsToDexterity(self):
        """Migrate MeetingConfig instances from Archetypes OrderedBaseFolder
        to Dexterity Container by re-applying the new DX FTI.

        Field data migration from AT storage to DX storage is handled by the
        Dexterity framework when objects are first accessed after the FTI switch.
        """
        logger.info('Re-applying MeetingConfig DX FTI...')
        load_type_from_package('MeetingConfig', 'Products.PloneMeeting:default')
        logger.info('Re-applying MeetingConfig DX FTI... Done.')

    def _migrateToolPloneMeetingToDexterity(self):
        """Copy AT camelCase attributes to DX snake_case attributes
        and clean up AT artifacts on ToolPloneMeeting."""
        logger.info('Migrating ToolPloneMeeting AT attrs to DX...')
        tool = self.portal.portal_plonemeeting
        for at_name, dx_name in _TOOL_AT_TO_DX.items():
            old_val = getattr(tool, at_name, None)
            if old_val is not None and not hasattr(tool, dx_name):
                if isinstance(old_val, (list, tuple)):
                    old_val = list(old_val)
                setattr(tool, dx_name, old_val)
                logger.info('  %s -> %s' % (at_name, dx_name))
            if hasattr(tool, at_name) and at_name != dx_name:
                delattr(tool, at_name)
        if hasattr(tool, 'enableScanDocs'):
            delattr(tool, 'enableScanDocs')
        for attr in _AT_ARTIFACTS:
            if hasattr(tool, attr):
                try:
                    delattr(tool, attr)
                except AttributeError:
                    pass
        load_type_from_package('ToolPloneMeeting', 'Products.PloneMeeting:default')
        logger.info('Migrating ToolPloneMeeting AT attrs to DX... Done.')

    def run(self, extra_omitted=[], from_migration_to_4200=False):
        logger.info('Migrating to PloneMeeting 4300...')
        self._migrateMeetingConfigsToDexterity()
        self._migrateToolPloneMeetingToDexterity()
        logger.info('Migrating to PloneMeeting 4300... Done.')


def migrate(context):
    '''This migration function will:

       1) Migrate MeetingConfig portal type from Archetypes to Dexterity
          by re-applying the new DX FTI.
       2) Migrate ToolPloneMeeting fields from AT camelCase to DX snake_case.
    '''
    migrator = Migrate_To_4300(context)
    migrator.run()
    migrator.finish()
