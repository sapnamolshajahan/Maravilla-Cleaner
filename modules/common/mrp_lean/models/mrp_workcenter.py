# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MRPWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    track_lean = fields.Boolean(string='Track for LEAN Reporting')
