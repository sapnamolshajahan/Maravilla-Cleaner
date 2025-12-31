# -*- coding: utf-8 -*-
from odoo import models, fields


class StockQuant(models.Model):
    _inherit = "stock.quant"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    def _get_avail_qty(self):
        for quant in self:
            quant.avail_qty = quant.quantity - quant.reserved_quantity

    ###########################################################################
    # Fields
    ###########################################################################
    avail_qty = fields.Float(compute="_get_avail_qty", string="Available Quantity")
