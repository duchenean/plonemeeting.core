# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from Products.Five import BrowserView


class PloneMeetingMacros(BrowserView):
    """
      Manage macros used for PloneMeeting.
    """

    __allow_access_to_unprotected_subobjects__ = 1

    def __getitem__(self, name):
        return self.index.macros[name]

    def callMacro(self, page, macro):
        """
          Call the given p_macro on given p_page (that is a BrowserView containing macros)
        """
        return self.context.unrestrictedTraverse(page)[macro]
