# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    def _set_user(self):
        for record in self:
            user = self.env['res.users'].search([('partner_id', '=', record.res_partner_id.id)])
            if user:
                record.user_id = user[0].id
            else:
                record.user_id = False

    user_id = fields.Many2one('res.users', string='User', compute='_set_user', store=True)

    def action_close(self):
        for record in self:
            record.is_read = True
