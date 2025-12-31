# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MRPWorkorderr(models.Model):
    _inherit = 'mrp.workorder'

    lean_status = fields.Selection(string='LEAN Status', selection=[('0','None'), ('1', 'On Time'), ('2', 'At Risk'), ('3', 'Cannot Meet')])
