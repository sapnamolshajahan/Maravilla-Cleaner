# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "res.company"

    ################################################################################
    # Fields
    ################################################################################
    sale_order_notice = fields.Text(string="Notice on Sales Order Reports")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ################################################################################
    # Fields
    ################################################################################
    sale_order_notice = fields.Text(related="company_id.sale_order_notice", readonly=False)
