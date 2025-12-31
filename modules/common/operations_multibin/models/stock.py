# -*- coding: utf-8 -*-
from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    warehouses = fields.One2many(comodel_name="stock.warehouse", inverse_name="lot_stock_id", string="Warehouses")
