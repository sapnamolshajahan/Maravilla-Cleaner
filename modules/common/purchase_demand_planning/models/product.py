# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    ################################################################################
    # Fields
    ###############################################################################
    indent_product = fields.Boolean(string="Indent Product")
