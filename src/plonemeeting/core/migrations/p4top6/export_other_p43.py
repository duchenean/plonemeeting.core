# -*- coding: utf-8 -*-
"""Export the data that is not content, on the Plone 4.3 side.

Companion of export_p43.py. Copy this file to the 4.3 server, then run:

    bin/instance run export_other_p43.py [name ...]

With no argument every export runs. The names are the keys of EXPORTS
plus "tool" and "registry". Each export writes one JSON file in var/instance/ or in
COLLECTIVE_EXPORTIMPORT_CENTRAL_DIRECTORY.

Environment: PM_EXPORT_SITE_ID (default "Plone", a path such as
"demo/demo" when the site is in a mounted database).
"""

from __future__ import absolute_import
from __future__ import print_function

from AccessControl.SecurityManagement import newSecurityManager
from plone.browserlayer.utils import registered_layers
from Testing.makerequest import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
from zope.interface import alsoProvides
from zope.interface.interfaces import IInterface

import json
import logging
import os
import sys
import transaction


logger = logging.getLogger("plonemeeting.core: p4top6 export")

try:
    STRING_TYPES = basestring  # noqa: F821 (python 2)
except NameError:
    # the script runs on the 4.3 server, its helpers are tested on 6.1
    STRING_TYPES = str

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

# plone.registry records that hold state the 4.3 site built at runtime,
# in the order they must be written back. "organizations" comes first:
# its vocabulary is every organization of the directory, while the rows
# of "functions" point at the *selected* organizations. Extend the list
# for a profile package that keeps more settings in the registry.
REGISTRY_RECORDS = (
    "collective.contact.plonegroup.browser.settings."
    "IContactPlonegroupConfig.organizations",
    "collective.contact.plonegroup.browser.settings."
    "IContactPlonegroupConfig.functions",
    "collective.contact.plonegroup.browser.settings."
    "IContactPlonegroupConfig.groups_management",
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


def plain(value):
    """Make p_value a plain JSON type. A registry value comes back as a
       persistent container, which the JSON encoder does not know."""
    if isinstance(value, STRING_TYPES):
        return value
    if hasattr(value, "keys"):
        return dict((key, plain(value[key])) for key in value.keys())
    if isinstance(value, (list, tuple, set, frozenset)) or \
            hasattr(value, "__iter__"):
        return [plain(sub) for sub in value]
    return value


def export_registry(portal):
    """Dump the plone.registry records of REGISTRY_RECORDS.

       collective.exportimport has no registry exporter, and the
       organizations and suffixes of collective.contact.plonegroup are
       registry records, not content: without them the new site has no
       selected organization, so no Plone group and no vocabulary for
       the fields that point at an organization."""
    registry = portal.portal_registry
    data = []
    for name in REGISTRY_RECORDS:
        if name not in registry.records:
            logger.warning("The registry has no record %s", name)
            continue
        value = plain(registry[name])
        data.append({"name": name, "value": value})
        logger.info("Exported the registry record %s (%s)",
                    name, isinstance(value, list) and len(value) or value)
    path = os.path.join(export_directory(), "registry.json")
    with open(path, "w") as dump:
        json.dump(data, dump, sort_keys=True, indent=4, default=str)
    logger.info("Exported %s registry records to %s", len(data), path)


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

    wanted = args or ["tool", "registry"] + [name for name, view in EXPORTS]
    for name in wanted:
        if name == "tool":
            export_tool(portal)
            continue
        if name == "registry":
            export_registry(portal)
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
