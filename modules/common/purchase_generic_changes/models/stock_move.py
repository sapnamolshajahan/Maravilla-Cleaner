# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # Add index
    created_purchase_line_ids = fields.Many2many(
        'purchase.order.line', 'stock_move_created_purchase_line_rel',
        'move_id', 'created_purchase_line_id', 'Created Purchase Order Lines', ondelete="restrict", index=True,
        readonly=True, copy=False)
