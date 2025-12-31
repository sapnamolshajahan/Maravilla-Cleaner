# -*- coding: utf-8 -*-
from odoo import fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    analysis_code = fields.Many2one(string="Analysis Code", related='product_id.product_analysis', store=True)
