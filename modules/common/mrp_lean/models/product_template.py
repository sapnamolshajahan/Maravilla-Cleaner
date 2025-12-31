# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    track_lean = fields.Boolean(string='Track for LEAN Reporting')
