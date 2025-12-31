# -*- coding: utf-8 -*-
from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    ###########################################################################
    # Fields
    ###########################################################################
    packing_printer = fields.Char("Packing Slip/Put-away Printer")
    picking_printer = fields.Char("Picking List Printer")
