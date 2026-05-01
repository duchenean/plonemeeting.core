# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from imio.helpers.setup import load_type_from_package
from plonemeeting.core.migrations import logger
from plonemeeting.core.migrations import Migrator


class Migrate_To_4217(Migrator):

    def run(self, extra_omitted=[], from_migration_to_4200=False):

        logger.info('Migrating to PloneMeeting 4217...')
        if not from_migration_to_4200:
            # re-apply POD templates types as edit action changed
            # as it is now reserved to Zope admin
            load_type_from_package('ConfigurablePODTemplate', 'plonemeeting.core:default')
            load_type_from_package('DashboardPODTemplate', 'plonemeeting.core:default')
            load_type_from_package('StyleTemplate', 'plonemeeting.core:default')
        logger.info('Migrating to PloneMeeting 4217... Done.')


def migrate(context):
    '''This migration function will:

       1) Re-apply PODTemplate related portal_types to change edit action.
    '''
    migrator = Migrate_To_4217(context)
    migrator.run()
    migrator.finish()
