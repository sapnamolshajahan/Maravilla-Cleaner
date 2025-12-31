# -*- coding: utf-8 -*-
from odoo import models, fields


class Company(models.Model):
    """
    Add Purchase Cover for products. Precedence (high to low) is:
        1. supplierinfo
        2. product category
        3. company
    """
    _inherit = "res.company"

    purchase_demand_cover = fields.Integer("Purchase Demand Cover", required=True, default=0,
                                           help="Days of Purchase Cover")
    history_count = fields.Integer(string="Demand History Months", required=True, default=24)
    forecast_count = fields.Integer(string="Forecast Months", required=True, default=1)
    plot_type = fields.Boolean(string="Plot Sale Demand Separate From Production Demand")
