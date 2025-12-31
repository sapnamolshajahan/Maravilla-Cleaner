# -*- coding: utf-8 -*-
from odoo import models, fields


class ForwardExchangeUpdate(models.Model):
    _name = "account.forward.exchange.update"
    _description = 'Forward Exchange Updates'

    name = fields.Char("Name")
    contract_no = fields.Char("Contract Number", size=256, required=True)
    due_date = fields.Date("Due Date", required=True)
    rate = fields.Float("Rate", digits=(18, 4), required=True)
    fe_contract = fields.Many2one("account.forward.exchange", "FE Contract")
