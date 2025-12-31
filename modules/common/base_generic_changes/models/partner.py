# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ################################################################################
    # Fields
    ################################################################################
    fax = fields.Char("Fax")
    known_as = fields.Char("Known As", size=50, help="Enter an alternative name")
