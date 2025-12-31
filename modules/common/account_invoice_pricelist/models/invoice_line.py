# -*- coding: utf-8 -*-
from odoo import api, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    @api.depends('product_id', 'product_uom_id', 'move_id.pricelist',)
    def _compute_price_unit(self):
        res = super(AccountInvoiceLine, self)._compute_price_unit()
        for line in self:
            if line.move_id.move_type != 'out_invoice':
                continue
            if line.product_id and line.move_id.pricelist:
                price = line.move_id.pricelist._get_product_price(line.product_id, line.quantity or 1.0)
                list_price = line.product_id.list_price
                if line.product_id.list_price:
                    discount = (line.product_id.list_price - price) / line.product_id.list_price * 100
                else:
                    discount = 0.0
                line.price_unit = list_price
                line.discount = discount
        return res
