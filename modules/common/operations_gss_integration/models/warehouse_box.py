# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GSSWarehouseBox(models.Model):
    _inherit = "stock.warehouse.box"

    package_code = fields.Many2one(string="Package Code", comodel_name="gss.package.code")
