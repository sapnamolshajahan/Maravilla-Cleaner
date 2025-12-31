# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplatePrecision(models.Model):
    _inherit = "product.template"

    normal_buy_price = fields.Float(string="Normal Buy Price", company_dependent=True, digits="Purchase Price",
                                    help="Product normal buy price.")

    standard_price = fields.Float(string="Cost", compute="_compute_standard_price",
                                  inverse="_set_standard_price", search="_search_standard_price",
                                  digits="Purchase Price", groups="base.group_user",
                                  help="Cost used for stock valuation in standard price "
                                       "and as a first price to set in average/fifo. "
                                       "Also used as a base price for pricelists. "
                                       "Expressed in the default unit of measure of the product. ")
