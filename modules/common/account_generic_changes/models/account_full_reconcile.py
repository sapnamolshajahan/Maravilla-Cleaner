# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountFullReconcile(models.Model):
    _inherit = 'account.full.reconcile'

    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name')
