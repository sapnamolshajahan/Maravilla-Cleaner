# -*- coding: utf-8 -*-
from odoo import models, fields

class InductionQuestions(models.Model):
    _name = 'induction.questions'
    _description = 'Induction Questions'
    _rec_name = 'induction_statement'

    induction_statement = fields.Char(string="Induction Statement", required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
