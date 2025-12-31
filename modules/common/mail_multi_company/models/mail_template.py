# -*- coding: utf-8 -*-
from odoo import  models, fields


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    company_id = fields.Many2one('res.company', string='Company', help='Leave blank to use for all companies')
