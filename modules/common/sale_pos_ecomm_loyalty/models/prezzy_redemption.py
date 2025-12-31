# -*- coding: utf-8 -*-
from odoo import fields, models


class PrezzyRedemption(models.Model):
    _name = 'prezzy.redemption'

    # Fields
    deduction_date = fields.Date(string='Date of request', default=False)
    partner_id = fields.Many2one('res.partner', string='User')
    deduction_amount = fields.Integer(string="Number of points deducted")
    card_value = fields.Float(string="Card value to issue")
    notes = fields.Char(string="Additional notes")
