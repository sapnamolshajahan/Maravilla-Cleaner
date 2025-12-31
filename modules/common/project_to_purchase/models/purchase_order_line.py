# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id', 'order_id.partner_id','order_id.account_analytic')
    def _compute_analytic_distribution(self):
        res = super(PurchaseOrderLine, self)._compute_analytic_distribution()
        for line in self:
            distribution = False
            if not line.display_type:
                if line.order_id.account_analytic:
                    distribution = line.order_id.account_analytic.id
                line.analytic_distribution = {distribution: 100} or line.analytic_distribution
        return res