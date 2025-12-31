# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def _stock_account_get_anglo_saxon_price_unit(self):
        self.ensure_one()

        bom = self.env["mrp.bom"].search([
            ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
            ("type", "=", "phantom"),
        ], limit=1)

        if bom and self.stock_move_id:
            stock_move_lines = self.env['stock.move'].search([
                ('sale_line_id', '=', self.stock_move_id.sale_line_id.id)
            ])

            if stock_move_lines and self.quantity:
                accum_cost = 0.0
                # value is price_unit * qty
                for stock_move in stock_move_lines:
                    line_cost = stock_move.price_unit if stock_move.price_unit else stock_move.product_id.standard_price
                    accum_cost += stock_move.product_uom_qty * line_cost
                cost_price = accum_cost/self.quantity  # assumes no UOM conversions
                return cost_price
        else:
            return super(AccountInvoiceLine, self)._stock_account_get_anglo_saxon_price_unit()
