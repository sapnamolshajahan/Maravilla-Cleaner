# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    active = fields.Boolean(string='Active', default=True)
