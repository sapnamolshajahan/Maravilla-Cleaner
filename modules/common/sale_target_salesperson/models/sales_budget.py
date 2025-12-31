# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.tools.translate import _


class SaleSaleBudget(models.Model):
    _name = 'sale.sale.budget'
    _description = 'Sales Budget by Salesperson'

    partner_id = fields.Many2one(comodel_name="res.users", string="Salesperson",
                                 required=True)
    user_id = fields.Many2one('res.users', related='partner_id.user_id')
    date = fields.Date(string="Month", required=True)
    budget = fields.Float(string="Budget", required=True)
    margin = fields.Float(string='Margin')
