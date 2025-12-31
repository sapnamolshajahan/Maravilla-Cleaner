# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class MailTemplateDesign(models.Model):
    _name = 'mail.template.design'
    _description = 'Mass Mail Design'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################
    name = fields.Char(string='Name')
    body = fields.Text(string='Body')

    ###########################################################################
    # Model methods
    ###########################################################################
    def render_templates(self):
        for dt in self:
            mail_templates = self.env['mail.template'].search([('design_template', '=', dt.id)])
            mail_templates.merge_content_and_design()

