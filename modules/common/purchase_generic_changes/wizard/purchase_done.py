# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseDone(models.TransientModel):
    _name = "purchase.done"
    _description = "Purchase Done"

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=True,
        domain=[('state', 'not in', ('draft', 'purchase', 'cancel'))])

    def set_done(self):
        for line in self.purchase_id.order_line:
            line.write({'qty_invoiced': line.product_qty})

        self.purchase_id.write({'state': 'purchase'})
        return {"type": "ir.actions.act_window_close"}
