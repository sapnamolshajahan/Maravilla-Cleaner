# -*- coding: utf-8 -*-
from odoo import fields, models,api


class AccountBudgetReportItem(models.Model):
    _inherit = "account.report.budget.item"
    _rec_name = 'budget_id'