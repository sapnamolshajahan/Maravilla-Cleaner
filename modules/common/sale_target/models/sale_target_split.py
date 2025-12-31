# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleTargetSplit(models.Model):
    _name = 'sale.target.split'
    _description = 'Sale Target split by month'

    sale_target_year = fields.Many2one('sale.target.year', string='Year')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    work_days = fields.Integer(string='Work Days')
    weighting = fields.Float(string='Weighting')
