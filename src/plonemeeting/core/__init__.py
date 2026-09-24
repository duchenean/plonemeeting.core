# -*- coding: utf-8 -*-
#
# File: __init__.py
#
# GNU General Public License (GPL)
#

from __future__ import absolute_import, print_function

from AccessControl import allow_module
from AccessControl import allow_type
from datetime import datetime
from plone.registry.field import DisallowedProperty
from Products.CMFCore import DirectoryView
from Products.CMFPlone.utils import ToolInit
from plonemeeting.core.config import product_globals
from plonemeeting.core.config import PROJECTNAME
# P6 migration: Products.validation (AT validators) dropped.
# from Products.validation import validation
# from Products.validation.validators.BaseValidators import baseValidators
# from Products.validation.validators.BaseValidators import protocols
# from .validators import ATCertifiedSignaturesValidator

import logging


DirectoryView.registerDirectory('skins', product_globals)

logger = logging.getLogger('PloneMeeting')
logger.debug('Installing Product')


# this is necessary to be able to register custom validator for datagridfield
# we use it for validators.PloneGroupSettings validators,
# see https://github.com/collective/collective.z3cform.datagridfield/issues/14
DisallowedProperty('__provides__')


def initialize(context):
    """initialize product (called by zope)"""

    from plonemeeting.core import monkey  # noqa
    from . import ToolPloneMeeting

    # Initialize portal tools
    tools = [ToolPloneMeeting.ToolPloneMeeting]
    ToolInit(PROJECTNAME + ' Tools',
             tools=tools,
             icon='tool.gif').initialize(context)

    allow_module('collective.iconifiedcategory.safe_utils')
    allow_module('collective.contact.core.safe_utils')
    allow_module('collective.contact.plonegroup.safe_utils')
    allow_module('imio.annex.safe_utils')
    allow_module('imio.history.safe_utils')
    allow_module('plonemeeting.core.safe_utils')
    allow_module('plonemeeting.core.browser.meeting')
    allow_type(datetime)
