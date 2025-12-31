# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    division = fields.Many2one('account.analytic.account', string='Division')
    district = fields.Many2one('account.analytic.account', string='District')
