# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountInvoiceLineExtension(models.Model):
    _inherit = "account.move.line"

    price_unit = fields.Float(digits="Purchase Price")
