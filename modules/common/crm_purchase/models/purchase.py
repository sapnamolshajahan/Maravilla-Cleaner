# -*- coding: utf-8 -*-

from odoo import models,fields, tools, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    crm_lead = fields.Many2one('crm.lead', string='Opportunity')

    @api.model_create_multi
    def create(self, values):
        for value in values:
            if self.env.context.get('opportunity', None):
                value['crm_lead'] = self.env.context['opportunity']
        return super(PurchaseOrder, self).create(values)


