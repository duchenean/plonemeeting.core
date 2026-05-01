# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from collective.z3cform.datagridfield import DataGridFieldFactory
from plone import api
from Products.PloneMeeting.interfaces import IToolPloneMeeting
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.i18n import translate


class ToolEditForm(form.EditForm):

    schema = IToolPloneMeeting
    fields = field.Fields(IToolPloneMeeting)

    def update(self):
        self.fields['holidays'].widgetFactory = DataGridFieldFactory
        self.fields['config_groups'].widgetFactory = DataGridFieldFactory
        self.fields['advisers_config'].widgetFactory = DataGridFieldFactory
        super(ToolEditForm, self).update()

    @button.buttonAndHandler(u'Save', name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        tool = self.context
        error = tool.validate_holidays(data.get('holidays', []))
        if error:
            self.status = error
            return
        error = tool.validate_configGroups(data.get('config_groups', []))
        if error:
            self.status = error
            return
        error = tool.validate_advisersConfig(data.get('advisers_config', []))
        if error:
            self.status = error
            return
        self.applyChanges(data)
        tool._set_config_groups(tool.config_groups)
        tool.post_edit()
        api.portal.show_message(
            translate(u'Changes saved.', domain='PloneMeeting',
                      context=self.request),
            self.request)
        self.request.response.redirect(tool.absolute_url())

    @button.buttonAndHandler(u'Cancel', name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())
