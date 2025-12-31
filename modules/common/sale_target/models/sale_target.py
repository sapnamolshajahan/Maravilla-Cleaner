# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleTargetYear(models.Model):
    _name = 'sale.target.year'
    _description = 'Sale Target Year'

    name = fields.Integer(string='Financial Year', required=True)


class SaleTarget(models.Model):
    _name = 'sale.target'
    _description = 'Sale Target'
    _rec_name = 'sale_target_year'

    sale_target_year = fields.Many2one('sale.target.year', string='Year')
    salesperson = fields.Many2one('res.users', string='Salesperson')
    target = fields.Float(string='Annual Target')
