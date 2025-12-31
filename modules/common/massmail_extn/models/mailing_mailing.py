# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import api, fields, models, tools, _


class MassMailMailing(models.Model):
    _inherit = 'mailing.mailing'

    ###########################################################################
    # Default & compute methods
    ###########################################################################
    def _compute_mail_server_available(self):
        fallback_mail_server = self.env['ir.config_parameter'].sudo().get_param('mass_mailing.outgoing_mail_server')
        mail_server = self.env.company.marketing_mail_server

        for mailing in self:
            mailing.mail_server_available = (mail_server and mail_server.id) or fallback_mail_server

    def _get_default_mail_server_id(self):
        fallback_mail_server = self.env['ir.config_parameter'].sudo().get_param('mass_mailing.mail_server_id')
        mail_server = self.env.company.marketing_mail_server and self.env.company.marketing_mail_server.id
        mail_server = mail_server or fallback_mail_server

        try:
            server_id = literal_eval(mail_server) if mail_server else False
            return self.env['ir.mail_server'].search([('id', '=', server_id)]).id

        except ValueError:
            return False

    ###########################################################################
    # Fields
    ###########################################################################
    marketing_mail_server = fields.Many2one(
        comodel_name='ir.mail_server',
        default=lambda self: self.env.company.marketing_mail_server)
