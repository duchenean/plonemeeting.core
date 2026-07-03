# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from AccessControl import Unauthorized
from Products.CMFCore.utils import _checkPermission
from Products.CPUtils.Extensions.utils import _folder_position_typeaware
from Products.Five import BrowserView
from plonemeeting.core.config import AddAnnex
from plonemeeting.core.config import AddAnnexDecision


class FolderPositionTypeawareView(BrowserView):
    """Plone 6 replacement for the CPUtils folder_position_typeaware External Method.
    Moves an annex up/down within its container, skipping over items of a different
    portal_type (type-aware ordering). Requires AddAnnex or AddAnnexDecision on the item.
    """

    def __call__(self, position='', id=None):
        position = position or self.request.get('position', '')
        id = id or self.request.get('id')
        if not _checkPermission(AddAnnex, self.context) and \
                not _checkPermission(AddAnnexDecision, self.context):
            raise Unauthorized
        _folder_position_typeaware(self.context, position, id)
        template_id = self.request.get('template_id')
        if template_id:
            return self.request.response.redirect(template_id)
