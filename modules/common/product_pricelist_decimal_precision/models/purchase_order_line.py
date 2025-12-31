# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrderLinePrecision(models.Model):
    _inherit = "purchase.order.line"

    price_unit = fields.Float(string="Unit Price", required=True, digits="Purchase Price")

    def _get_stock_move_price_unit(self):
        price_unit = super(PurchaseOrderLinePrecision, self)._get_stock_move_price_unit()
        line = self[0]
        if line.taxes_id:
            if line.taxes_id[0].price_include:
                return price_unit

        if line.product_uom.id != line.product_id.uom_id.id:
            return price_unit

        return line.price_unit
