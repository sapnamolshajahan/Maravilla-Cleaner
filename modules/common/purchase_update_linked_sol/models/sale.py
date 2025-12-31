# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_order = fields.Many2one('purchase.order', string='Purchase Order', copy=False)

    def _prepare_procurement_values(self):
        ctx = self.env.context.copy()
        ctx['sale_line_id'] = self.id
        self = self.with_context(ctx)
        return super(SaleOrderLine, self)._prepare_procurement_values()
