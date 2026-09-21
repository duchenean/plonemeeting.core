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

Environment: PM_EXPORT_SITE_ID (default "Plone", a path such as
"demo/demo" when the site is in a mounted database),
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
from plone.browserlayer.utils import registered_layers
from Testing.makerequest import makerequest
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
from zope.interface import alsoProvides
from zope.interface.interfaces import IInterface

def script_and_args(argv):
    """Get the script path and its arguments.

       zopectl runs a script as [interpreter, "-c", <script>, <args>].
       A plain python run gives [<script>, <args>]."""
    if len(argv) > 2 and argv[1] == "-c":
        return argv[2], argv[3:]
    return argv[0], argv[1:]


SCRIPT, ARGS = script_and_args(sys.argv)

try:
    from plonemeeting.core.migrations.p4top6 import extra_state
except ImportError:
    # zopectl runs the script with the interpreter globals, so __file__ is
    # the interpreter. Use the script path to find the companion module.
    sys.path.insert(0, os.path.dirname(os.path.abspath(SCRIPT)))
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
    # A scripted request has no browser layer. Serializers and views that
    # are registered for a layer are not found without them, for example
    # the "conversation_view" that every plone.restapi serializer needs.
    for layer in registered_layers():
        # A layer of a package that is not installed comes back as a
        # broken class. Skip it.
        if IInterface.providedBy(layer):
            alsoProvides(request, layer)
        else:
            logger.warning("Skipped unavailable browser layer %r", layer)


def drop_restapi_serializers():
    """Remove the REST API serializers of the PloneMeeting packages.

       They give the reduced API representation of an object, which has
       no "parent" key and no workflow history. They are more specific
       than the plone.restapi serializers, so they win. The export needs
       the full plone.restapi representation."""
    from plone.restapi.interfaces import ISerializeToJson
    from plone.restapi.interfaces import ISerializeToJsonSummary
    from zope.component import getGlobalSiteManager

    serializers = (ISerializeToJson, ISerializeToJsonSummary)
    api_packages = ("plonemeeting.restapi", "imio.restapi")
    gsm = getGlobalSiteManager()
    for registration in list(gsm.registeredAdapters()):
        factory = registration.factory
        if registration.provided not in serializers:
            continue
        if not factory.__module__.startswith(api_packages):
            continue
        gsm.unregisterAdapter(factory,
                              registration.required,
                              registration.provided,
                              registration.name)
        logger.info("Dropped serializer %s.%s",
                    factory.__module__, factory.__name__)


def patch_richtext_serializer():
    """Make the collective.exportimport rich text serializer safe.

       It reads value.raw without a check. A Dexterity field that was
       never set gives NO_VALUE, which is true but has no raw."""
    from collective.exportimport.serializer import (
        RichttextFieldSerializerWithRawText)
    from plone.restapi.serializer.converters import json_compatible

    def __call__(self):
        value = self.get_value()
        raw = getattr(value, "raw", None)
        if raw is None:
            return None
        return {
            u"data": json_compatible(raw),
            u"content-type": json_compatible(value.mimeType),
            u"encoding": json_compatible(value.encoding),
        }

    RichttextFieldSerializerWithRawText.__call__ = __call__


def traverse_site(app, site_id):
    """Get the Plone site. p_site_id can be a path when the site is in a
       mounted database, for example "demo/demo"."""
    portal = app
    for name in site_id.strip("/").split("/"):
        portal = getattr(portal, name)
    return portal


def main(app, args):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    site_id = os.environ.get("PM_EXPORT_SITE_ID", "Plone")
    filename = os.environ.get("PM_EXPORT_FILENAME", "pm_content.json")
    app = makerequest(app)
    request = app.REQUEST
    setRequest(request)
    portal = traverse_site(app, site_id)
    setSite(portal)
    # run as the first Zope root user
    admin = app.acl_users.getUsers()[0]
    newSecurityManager(None, admin.__of__(app.acl_users))

    drop_restapi_serializers()
    patch_richtext_serializer()
    view = PMExportContent(portal, request)
    portal_types = args or portal_types_with_content(view, portal)
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
    main(app, ARGS)  # noqa: F821
