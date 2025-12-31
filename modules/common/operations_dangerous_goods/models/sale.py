# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ################################################################################
    # Fields
    ################################################################################
    dangerous_goods_type = fields.Selection(related="partner_id.dangerous_goods_type", string="Dangerous Goods Licence")
    dg_expiry_date = fields.Date(string="Expiry Date", related="partner_id.dg_expiry_date")
