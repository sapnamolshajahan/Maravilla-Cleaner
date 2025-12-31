# -*- coding: utf-8 -*-
from odoo import models, api


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        vals_length = len(vals_list)
        for i in reversed(range(0, vals_length)):
            if vals_list[i].get('mail_message_id', None):
                mail_message = self.env['mail.message'].browse(vals_list[i]['mail_message_id'])
                if mail_message:
                    model_id = self.env['ir.model'].search([('model', '=', mail_message.model)], limit=1)
                    if model_id and not model_id.block_internal_notification:
                        new_vals_list.append(vals_list[i])
                    elif mail_message.message_type != 'user_notification':
                        new_vals_list.append(vals_list[i])
                    elif not model_id:
                        new_vals_list.append(vals_list[i])

        return super(MailNotification, self).create(new_vals_list)
