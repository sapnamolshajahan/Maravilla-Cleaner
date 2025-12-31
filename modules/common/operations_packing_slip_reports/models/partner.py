# -*- coding: utf-8 -*-
from odoo import fields, models


class Partner(models.Model):
    """
    Partner packing slip pricing preference.
    """
    _inherit = "res.partner"

    ################################################################################
    # Fields
    ################################################################################
    packing_slip_pricing = fields.Selection(
        [
            ("unpriced", "Unpriced"),
            ("priced", "Priced"),
        ], default="unpriced", required=True, string="Packing Slip")
