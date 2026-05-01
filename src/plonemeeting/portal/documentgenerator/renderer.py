# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from collective.documentgenerator.interfaces import IFieldRendererForDocument
from zope.component import queryUtility
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory


@implementer(IFieldRendererForDocument)
class ATFieldStubRenderer(object):
    """IFieldRendererForDocument adapter for _ATFieldStub + _ATFieldWidgetStub.

    Bridges the documentgenerator rendering chain for the DX MeetingItem
    which returns AT-compat stub objects from ``getField()``.
    """

    def __init__(self, field, widget, context):
        self.field = field
        self.widget = widget
        self.context = context
        self.helper_view = None

    def render(self, no_value=''):
        if self.has_no_value():
            return no_value
        return self.render_value()

    def render_value(self):
        value = self.field.get(self.context)
        if value is None:
            return u''
        from plonemeeting.portal.content.meetingconfig import _at_to_dx
        from plonemeeting.portal.content.meetingitem import IMeetingItem
        dx_name = _at_to_dx(self.field._field_name)
        schema_field = IMeetingItem.get(dx_name)
        if schema_field is not None:
            vocab_name = getattr(schema_field, 'vocabularyName', None) or \
                getattr(schema_field, 'vocabulary', None)
            if not vocab_name and hasattr(schema_field, 'value_type'):
                vocab_name = getattr(schema_field.value_type, 'vocabularyName', None) or \
                    getattr(schema_field.value_type, 'vocabulary', None)
            if vocab_name:
                factory = queryUtility(IVocabularyFactory, name=vocab_name)
                if factory is not None:
                    vocab = factory(self.context)
                    try:
                        return vocab.getTerm(value).title or value
                    except LookupError:
                        pass
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    def has_no_value(self):
        value = self.field.get(self.context)
        return not bool(value)
