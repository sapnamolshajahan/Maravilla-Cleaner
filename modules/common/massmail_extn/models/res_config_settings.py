# -*- coding: utf-8 -*-
from odoo import fields, models, api


class MassMailSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ###########################################################################
    # Default & compute methods
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################
    marketing_mail_server = fields.Many2one(
        string='Default Mail Server for Email Marketing',
        comodel_name='ir.mail_server')

    ###########################################################################
    # Methods
    ###########################################################################
    def set_values(self):
        super(MassMailSettings, self).set_values()
        self.env.company.write({"marketing_mail_server": self.marketing_mail_server})

    def get_values(self):
        res = super(MassMailSettings, self).get_values()
        company = self.env.company
        res.update({"marketing_mail_server": company.marketing_mail_server})
        return res
