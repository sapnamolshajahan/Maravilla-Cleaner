# -*- coding: utf-8 -*-
from odoo import models, fields


class SupplierInfo(models.Model):
    """
    Add Purchase Cover for products. Precedence (high to low) is:
        1. supplierinfo
        2. product category
        3. company
    """
    _inherit = "product.supplierinfo"

    ################################################################################
    # Fields
    ################################################################################
    purchase_demand_cover = fields.Integer("Purchase Demand Cover", required=True, default=0,
                                           help="Days of Purchase Cover")
