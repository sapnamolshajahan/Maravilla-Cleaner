# -*- coding: utf-8 -*-
from odoo import fields, models


class HrKeyDescription(models.Model):
    _name = "hr.key.description"
    _description = "Key Description"

    ###########################################################################
    # Fields
    ###########################################################################

    name = fields.Char(string="Key name", required=True, help="Name of the Key.")
    active = fields.Boolean(string="Active", help="Indicates whether the Key is active or not.", default=True)
