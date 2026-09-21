# -*- coding: utf-8 -*-
"""Export the data that is not content, on the Plone 4.3 side.

Companion of export_p43.py. Copy this file to the 4.3 server, then run:

    bin/instance run export_other_p43.py [name ...]

With no argument every export runs. The names are the keys of EXPORTS
plus "tool". Each export writes one JSON file in var/instance/ or in
COLLECTIVE_EXPORTIMPORT_CENTRAL_DIRECTORY.

Environment: PM_EXPORT_SITE_ID (default "Plone", a path such as
"demo/demo" when the site is in a mounted database).
"""

from __future__ import absolute_import
from __future__ import print_function

import json
import logging
import os
import sys

import transaction

from AccessControl.SecurityManagement import newSecurityManager
from plone.browserlayer.utils import registered_layers
from Testing.makerequest import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
from zope.interface import alsoProvides
from zope.interface.interfaces import IInterface

logger = logging.getLogger("plonemeeting.core: p4top6 export")

# export name -> collective.exportimport view
EXPORTS = (
    ("relations", "@@export_relations"),
    ("members", "@@export_members"),
    ("localroles", "@@export_localroles"),
    ("ordering", "@@export_ordering"),
    ("defaultpages", "@@export_defaultpages"),
    ("redirects", "@@export_redirects"),
    ("portlets", "@@export_portlets"),
)

# portal_plonemeeting: AT accessor -> Dexterity attribute
TOOL_FIELDS = (
    ("getMeetingFolderTitle", "meeting_folder_title"),
    ("getFunctionalAdminEmail", "functional_admin_email"),
    ("getFunctionalAdminName", "functional_admin_name"),
    ("getRestrictUsers", "restrict_users"),
    ("getUnrestrictedUsers", "unrestricted_users"),
    ("getWorkingDays", "working_days"),
    ("getHolidays", "holidays"),
    ("getDelayUnavailableEndDays", "delay_unavailable_end_days"),
    ("getConfigGroups", "config_groups"),
    ("getDeferParentReindex", "defer_parent_reindex"),
    ("getShowExternalLinksSection", "show_external_links_section"),
    ("getAdvisersConfig", "advisers_config"),
)


def script_and_args(argv):
    """Get the script path and its arguments.

       zopectl runs a script as [interpreter, "-c", <script>, <args>].
       A plain python run gives [<script>, <args>]."""
    if len(argv) > 2 and argv[1] == "-c":
        return argv[2], argv[3:]
    return argv[0], argv[1:]


SCRIPT, ARGS = script_and_args(sys.argv)


def traverse_site(app, site_id):
    """Get the Plone site. p_site_id can be a path when the site is in a
       mounted database, for example "demo/demo"."""
    portal = app
    for name in site_id.strip("/").split("/"):
        portal = getattr(portal, name)
    return portal


def prepare_request(request, portal):
    """Make p_request look like a submitted collective.exportimport form."""
    request.environ["REQUEST_METHOD"] = "POST"
    try:
        request.method = "POST"
    except AttributeError:
        pass
    request.form["form.submitted"] = True
    request["ACTUAL_URL"] = portal.absolute_url()
    for layer in registered_layers():
        # A layer of a package that is not installed comes back as a
        # broken class. Skip it.
        if IInterface.providedBy(layer):
            alsoProvides(request, layer)
        else:
            logger.warning("Skipped unavailable browser layer %r", layer)


def export_directory():
    """Get the directory the JSON files go to."""
    from App.config import getConfiguration
    from collective.exportimport import config

    return config.CENTRAL_DIRECTORY or getConfiguration().clienthome


def export_tool(portal):
    """Dump the portal_plonemeeting settings.

       portal_plonemeeting is a tool, not content, so
       collective.exportimport cannot export it."""
    tool = portal.portal_plonemeeting
    data = {}
    missing = []
    for accessor, attribute in TOOL_FIELDS:
        if not hasattr(tool, accessor):
            missing.append(accessor)
            continue
        data[attribute] = getattr(tool, accessor)()
    if missing:
        logger.warning("The tool has no accessor %s", ", ".join(missing))
    # report the row keys of the grids, they must match the Dexterity ones
    for attribute in ("holidays", "config_groups", "advisers_config"):
        rows = data.get(attribute) or ()
        if rows:
            logger.info("%s row keys: %s", attribute, sorted(rows[0].keys()))
    path = os.path.join(export_directory(), "tool.json")
    with open(path, "w") as dump:
        json.dump(data, dump, sort_keys=True, indent=4, default=str)
    logger.info("Exported %s fields of the tool to %s", len(data), path)


def main(app, args):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    site_id = os.environ.get("PM_EXPORT_SITE_ID", "Plone")
    app = makerequest(app)
    request = app.REQUEST
    setRequest(request)
    portal = traverse_site(app, site_id)
    setSite(portal)
    # run as the first Zope root user
    admin = app.acl_users.getUsers()[0]
    newSecurityManager(None, admin.__of__(app.acl_users))
    prepare_request(request, portal)

    wanted = args or ["tool"] + [name for name, view in EXPORTS]
    for name in wanted:
        if name == "tool":
            export_tool(portal)
            continue
        view_name = dict(EXPORTS).get(name)
        if view_name is None:
            logger.error("There is no export named %s", name)
            continue
        logger.info("Running %s", view_name)
        request.form["filename"] = "{0}.json".format(name)
        view = portal.restrictedTraverse(view_name)
        view(download_to_server=True)
    # the export must not change the source database
    transaction.abort()


if __name__ == "__main__":
    main(app, ARGS)  # noqa: F821
