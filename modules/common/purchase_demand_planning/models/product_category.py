# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    """
    Add Purchase Cover for products. Precedence (high to low) is:
        1. supplierinfo
        2. product category
        3. company
    """
    _inherit = "product.category"

    purchase_demand_cover = fields.Integer("Purchase Demand Cover", required=True, default=0,
                                           help="Days of Purchase Cover")
