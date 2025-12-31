# -*- coding: utf-8 -*-
from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_analysis = fields.Many2one(comodel_name="product.analysis.type", string="Analysis Type",
                                       related='product_id.product_analysis', store=True)
