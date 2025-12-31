# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrderValue(models.TransientModel):
    """
    Allows you to set a specific untaxed amount for the current Purchase Order, this is then portioned
    across all the Purchase Order Lines pro rata.
    """
    _name = "purchase.purchase_order_value"

    purchase = fields.Many2one("purchase.order", string="Purchase Order", required=True)
    value = fields.Float(string="New Amount", digits="Purchase Price", required=True,
                         help=("The new untaxed amount of the Purchase Order, "
                               "to be portioned pro rata across the Purchase Order Lines."))

    def button_update_purchase_order_value(self):

        purchase_order = self.purchase
        for purchase_order_value in self:
            amount_untaxed = purchase_order.amount_untaxed
            currency_id = purchase_order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            if purchase_order.order_line:
                last_line_id = purchase_order.order_line[-1:][0].id
                total = 0.0

                for order_line in purchase_order.order_line:
                    old_price = order_line.price_unit * order_line.product_qty
                    new_price = currency_id.round(old_price / amount_untaxed * purchase_order_value.value)
                    new_unit_price = currency_id.round(new_price / order_line.product_qty)
                    order_line.price_unit = new_unit_price

                    total += (new_unit_price * order_line.product_qty)

                    if order_line.id == last_line_id:
                        rounding_diff = currency_id.round((purchase_order_value.value - total) / order_line.product_qty)
                        order_line.price_unit += rounding_diff

                    order_line.write({"price_unit": order_line.price_unit})
        return {"type": "ir.actions.act_window_close"}
