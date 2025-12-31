# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    crm_lead = fields.Many2one('crm.lead', string='Opportunity')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('project_id', None):
                project = self.env['project.project'].browse(vals['project_id'])
                if project.crm_lead and not project.crm_won:
                    vals['crm_lead'] = project.crm_lead.id
            if not vals.get('product_uom_id', None):
                vals['product_uom_id'] = self.env.company.project_time_mode_id.id
        return super(AccountAnalyticLine, self).create(vals_list)
