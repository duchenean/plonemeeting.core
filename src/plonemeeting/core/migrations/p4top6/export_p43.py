# -*- coding: utf-8 -*-
"""Export script for the Plone 4.3 side of the P4 -> P6 migration.

Runs collective.exportimport's @@export_content with the PloneMeeting
extra state added to every exported item (see extra_state.py). Copy
this file and extra_state.py to the 4.3 server, then run:

    bin/instance -O Plone run export_p43.py [portal_type ...]

With no portal_type argument, every type that has content is exported.
Blobs are exported as blob paths (include_blobs=2) and the JSON is
written to var/instance/<filename>.json (or to
COLLECTIVE_EXPORTIMPORT_CENTRAL_DIRECTORY when set).

Environment: PM_EXPORT_SITE_ID (default "Plone"),
PM_EXPORT_FILENAME (default "pm_content.json").
"""

from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import sys

import transaction

from AccessControl.SecurityManagement import newSecurityManager
from collective.exportimport.export_content import ExportContent
from Testing.makerequest import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest

try:
    from plonemeeting.core.migrations.p4top6 import extra_state
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import extra_state

logger = logging.getLogger("plonemeeting.core: p4top6 export")


class PMExportContent(ExportContent):
    """@@export_content plus the PloneMeeting extra state."""

    def global_dict_hook(self, item, obj):
        item[extra_state.EXTRA_STATE_KEY] = extra_state.dump_extra_state(obj)
        return item


def portal_types_with_content(view, portal):
    """Return every portal_type that has content, as the export form
       lists them. The view query attributes are only set by __call__,
       so set them first."""
    view.portal_type = []
    view.path = "/".join(portal.getPhysicalPath())
    view.depth = -1
    return [info["value"] for info in view.portal_types()]


def prepare_request(request, portal, filename):
    """Make p_request look like the submitted @@export_content form.
       A scripted request is a GET by default and the export view then
       forces migration=True, which drops the relation fields."""
    request.environ["REQUEST_METHOD"] = "POST"
    try:
        request.method = "POST"
    except AttributeError:
        pass
    request.form["form.submitted"] = True
    request.form["filename"] = filename
    request.form["write_errors"] = True
    request["ACTUAL_URL"] = portal.absolute_url()


def main(app, argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    site_id = os.environ.get("PM_EXPORT_SITE_ID", "Plone")
    filename = os.environ.get("PM_EXPORT_FILENAME", "pm_content.json")
    app = makerequest(app)
    request = app.REQUEST
    setRequest(request)
    portal = getattr(app, site_id)
    setSite(portal)
    # run as the first Zope root user
    admin = app.acl_users.getUsers()[0]
    newSecurityManager(None, admin.__of__(app.acl_users))

    view = PMExportContent(portal, request)
    portal_types = argv[1:] or portal_types_with_content(view, portal)
    logger.info("Exporting %s", ", ".join(portal_types))
    prepare_request(request, portal, filename)
    view(portal_type=portal_types,
         include_blobs=2,
         download_to_server=True,
         migration=False,
         write_errors=True)
    # export must not change the source database
    transaction.abort()


if __name__ == "__main__":
    main(app, sys.argv)  # noqa: F821
