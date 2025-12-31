# -*- coding: utf-8 -*-
from odoo import models, fields


class Product(models.Model):
    """
        Product with bin locations.
    """
    _inherit = "product.product"

    ###########################################################################
    # Fields
    ###########################################################################

    bin_ids = fields.One2many(comodel_name="stock.warehouse.bin", inverse_name="product_id", string="Bins")


class ProductTemplate(models.Model):
    """
        Product with bin locations.
    """
    _inherit = "product.template"

    ###########################################################################
    # Fields
    ###########################################################################

    bin_ids = fields.One2many(comodel_name="stock.warehouse.bin", inverse_name="product_template_id", string="Bins")
