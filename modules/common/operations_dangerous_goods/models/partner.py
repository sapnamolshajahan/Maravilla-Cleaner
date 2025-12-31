# -*- coding: utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _inherit = "res.partner"

    # Fields
    dangerous_goods_type = fields.Selection(
        [
            ("d", "Dangerous Goods Driving Endorsement"),
            ("a", "Allowed to handle type1"),
            ("b", "Allowed to handle type2")
        ], string="Dangerous Goods Licence")
    dg_expiry_date = fields.Date(string="Expiry Date")
