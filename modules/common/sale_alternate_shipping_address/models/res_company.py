# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    show_hide_alt_so_address = fields.Boolean(string='Show Alt Delivery Address by Default')
