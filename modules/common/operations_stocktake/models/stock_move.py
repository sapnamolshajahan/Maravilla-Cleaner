# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    ###########################################################################
    # Fields
    ###########################################################################
    inventory_line = fields.Many2one("stock.inventory.line", string="Line Adjustment Source")
    inventory_id = fields.Many2one("stock.inventory", string="Inventory")
