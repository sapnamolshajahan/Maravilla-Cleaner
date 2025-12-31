# -*- coding: utf-8 -*-
from odoo import models, fields

class VisitorType(models.Model):
    _name = 'visitor.type'
    _description = 'Visitor Type'

    name = fields.Char(string="Visitor Type", required=True)
    induction_question_ids = fields.Many2many('induction.questions',string="Induction Questions")
