# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    show_hide_alt_po_address = fields.Boolean(string='Show Alt Delivery Address by Default on PO')
