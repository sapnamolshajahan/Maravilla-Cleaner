# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductSupplierinfoPrecision(models.Model):
    _inherit = "product.supplierinfo"

    price = fields.Float(string="Price", default=0.0, digits="Purchase Price", required=True,
                         help="The price to purchase a product")
