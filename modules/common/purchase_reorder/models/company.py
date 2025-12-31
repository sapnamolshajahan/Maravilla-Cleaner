# -*- coding: utf-8 -*-
from odoo import models, fields


class Company(models.Model):
    """
    Add Purchase Cover for products. Precedence (high to low) is:
        1. supplierinfo
        2. product category
        3. company
    """
    _inherit = "res.company"

    default_warehouse = fields.Many2one("stock.warehouse", string='Default Warehouse', help='Warehouse used for reorder rules')


