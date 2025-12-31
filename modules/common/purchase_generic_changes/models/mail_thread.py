# -*- encoding: utf-8 -*-
from odoo import _, api, fields, models, SUPERUSER_ID


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=None):
        """Modify context so no link to the document is auto-inserted in emails sent"""
        groups = super(MailThread, self)._notify_get_recipients_groups(message, model_description, msg_vals=msg_vals)
        for _group_name, _group_method, group_data in groups:
            group_data['has_button_access'] = False

        return groups

    def _notify_get_recipients_classify(self, message, recipients_data,
                                        model_description, msg_vals=None):
        """ Modify context so no link to the document is auto-inserted in emails sent"""
        groups = super(MailThread, self)._notify_get_recipients_classify(message, recipients_data,
                                        model_description, msg_vals=msg_vals)

        for group in groups:
            group["has_button_access"] = False
            group["button_access"] = {}

        return groups
