# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    disable_auto_packing_slip = fields.Boolean(
        string="Don't auto-print Packing Slip",
        help='If checked, packing slips will not be automatically printed for this customer'
    )