# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    stock_receovery_account = fields.Many2one('account.account', string='Stock Reoovery Account')
