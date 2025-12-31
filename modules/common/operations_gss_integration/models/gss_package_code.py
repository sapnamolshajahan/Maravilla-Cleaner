# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GSSPackageCodes(models.Model):
    _name = "gss.package.code"
    _description = "Package Codes for GSS"

    name = fields.Char(string="Code", required=True)
    description = fields.Char(string="Description/Notes")
