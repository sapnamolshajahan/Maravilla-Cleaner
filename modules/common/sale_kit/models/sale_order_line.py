# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    override_qty_delivered = fields.Boolean(string='Override Qty Delivered')
    manual_qty_delivered = fields.Float(string='Manual Qty Delivered')

    @api.depends('move_ids.state', 'move_ids.quantity', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self:
            if line.override_qty_delivered:
                line.qty_delivered = line.manual_qty_delivered
