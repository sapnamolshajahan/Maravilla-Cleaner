# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # override the standard column definitions with our own specifying the all important
    # "Purchase Price" decimal precision
    price_surcharge = fields.Float("Price Surcharge",
                                   help="Specify the fixed amount to add or subtract(if negative) to the amount "
                                        "calculated with the discount.",
                                   digits="Purchase Price")
    price_round = fields.Float("Price Rounding", digits="Purchase Price",
                               help="Sets the price so that it is a multiple of this value.  "
                                    "Rounding is applied after the discount and before the surcharge. "
                                    "To have prices that end in 9.99, set rounding 10, surcharge -0.01")
    price_min_margin = fields.Float("Min. Price Margin", digits="Purchase Price")
    price_max_margin = fields.Float("Max. Price Margin", digits="Purchase Price")
    fixed_price = fields.Float("Fixed Price", digits="Purchase Price")
