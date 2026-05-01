# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from imio.helpers.setup import load_type_from_package
from plonemeeting.portal.migrations import logger
from plonemeeting.portal.migrations import Migrator


class Migrate_To_4212(Migrator):

    def _enableUseridBehaviorForPerson(self):
        """Field person.userid is now managed by a behavior from
           collective.contact.plonegroup, moreover there is a userid catalog index."""
        logger.info('Enabling "userid" behavior for "person"...')
        load_type_from_package('person', 'plonemeeting.portal:default')
        self.reindexIndexesFor(idxs=['userid'], **{'portal_type': ['person']})
        logger.info('Done.')

    def run(self, extra_omitted=[], from_migration_to_4200=False):

        logger.info('Migrating to PloneMeeting 4212...')
        if not from_migration_to_4200:
            # this will upgrade collective.contact.plonegroup especially
            self.upgradeAll(omit=['plonemeeting.portal:default',
                                  self.profile_name.replace('profile-', '')])
            self._enableUseridBehaviorForPerson()
        logger.info('Migrating to PloneMeeting 4212... Done.')


def migrate(context):
    '''This migration function will:

       1) Enable "userid" behavior for "person".
    '''
    migrator = Migrate_To_4212(context)
    migrator.run()
    migrator.finish()
