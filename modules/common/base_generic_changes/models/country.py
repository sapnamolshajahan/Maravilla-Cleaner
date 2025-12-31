# -*- coding: utf-8 -*-
from odoo import fields, models


class Country(models.Model):
    _inherit = "res.country"

    ################################################################################
    # Fields
    ################################################################################
    company_tax_name = fields.Char("Company Tax Name", help="Tax Name used on invoices, eg: GST, ABN")
