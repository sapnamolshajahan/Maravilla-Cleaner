# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductAnalysisCode(models.Model):
    _name = "product.analysis.type"
    _description = "Product Analysis Type"

    name = fields.Char("Name")


class Product(models.Model):
    _inherit = "product.template"

    product_analysis = fields.Many2one(comodel_name="product.analysis.type", string="Analysis Type")

