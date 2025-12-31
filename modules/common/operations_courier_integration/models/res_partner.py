# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    building = fields.Char("Building", help="Building info like unit, level, building/complex name")
