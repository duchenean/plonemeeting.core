from __future__ import absolute_import, print_function

from Products.Five import BrowserView


class PloneMeetingMacros(BrowserView):
    """
      Manage macros used for PloneMeeting.
    """

    __allow_access_to_unprotected_subobjects__ = 1
    __roles__ = None

    def __getitem__(self, name):
        macro = self.index.macros[name]
        # Chameleon macro functions may carry a PermissionRole __roles__ that
        # is not iterable in Python 3, causing AccessControl.validate to fail.
        # Set __roles__ to None so AccessControl treats the macro as public.
        try:
            macro.__roles__ = None
        except (AttributeError, TypeError):
            pass
        return macro

    def callMacro(self, page, macro):
        """
          Call the given p_macro on given p_page (that is a BrowserView containing macros)
        """
        return self.context.unrestrictedTraverse(page)[macro]
