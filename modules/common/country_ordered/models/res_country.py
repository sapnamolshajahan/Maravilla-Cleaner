# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCountryExtended(models.Model):
    _inherit = "res.country"
    _order = "sequence, name"

    ###########################################################################
    # Fields
    ###########################################################################
    sequence = fields.Integer(string="Sequence", required=True, default=50,
                              help="Set number to indicate the display sequence in selection and searches")
