# -*- coding: utf-8 -*-

from odoo.exceptions import UserError

from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    net_tax_amount = fields.Float("Net Tax Amount", digits='Accounting')


