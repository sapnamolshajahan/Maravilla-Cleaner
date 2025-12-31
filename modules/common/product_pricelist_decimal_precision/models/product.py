# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProductPrecision(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        'Cost', company_dependent=True,
        digits='Purchase Price',
        groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the last unit that left the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")
