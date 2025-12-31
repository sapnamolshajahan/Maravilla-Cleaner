# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VisitorLog(models.Model):
    _name = 'visitor.log'
    _description = 'Visitor Log'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone Number")
    visitor_type_id = fields.Many2one('visitor.type', string="Visitor Type")
    staff_member_id = fields.Many2one('hr.employee', string="Staff Member Visiting")
    induction_question_file = fields.Binary(string="Induction Questions (PDF)")
    induction_filename = fields.Char(string="File Name")

