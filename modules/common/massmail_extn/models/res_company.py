# -*- coding: utf-8 -*-
from odoo import fields, models, api


class MassMailCompany(models.Model):
    _inherit = 'res.company'

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
