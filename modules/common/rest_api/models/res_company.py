# -*- coding: utf-8 -*-
from odoo import fields, models


DATE_FORMATS = [
    ('%d/%m/%Y', 'dd/mm/YYYY'),
    ('%d-%m-%Y', 'dd-mm-YYYY'),
    ('%d/%B/%Y', 'dd/month/YYYY'),
    ('%d-%B-%Y', 'dd-month-YYYY'),
]


class ApiResCompanyFields(models.Model):
    _name = "res.company.api.fields"

    ######################################################
    # Default and compute methods
    ######################################################

    ######################################################
    # Fields
    ######################################################
    company = fields.Many2one(string='Company', comodel_name='res.company', ondelete='cascade')
    model = fields.Many2one(comodel_name='ir.model', string='Model')
    name = fields.Char(string='Name')
    value = fields.Char(string='Value')
    is_active = fields.Boolean(string='Active', default=True)

    ######################################################
    # Methods
    ######################################################


class ApiResCompany(models.Model):
    _inherit = "res.company"

    ######################################################
    # Default and compute methods
    ######################################################

    ######################################################
    # Fields
    ######################################################
    api_fields = fields.One2many(
        string='API Fields',
        help='Use this mapping if you would like to use another field as a unique reference instead of ID',
        comodel_name='res.company.api.fields',
        inverse_name='company')

    date_format = fields.Selection(selection=DATE_FORMATS, string='API Date Format')
    replace_false = fields.Boolean(string='Replace "false" with blank')

    ######################################################
    # Methods
    ######################################################
