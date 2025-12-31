# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    ###########################################################################
    # Fields
    ###########################################################################

    picking_wizard_sort = fields.Boolean(string="Sort on Picking Wizard", default=True,
                                         help="Enable/Disable multibin sorting on the Picking Wizard")
