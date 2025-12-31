# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class LetterTemplate(models.Model):
    _name = 'letter.template'
    _description = 'Letter Templates'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ###########################################################################
    # Fields
    ###########################################################################
    model_id = fields.Many2one(string="Model", comodel_name='ir.model')
    name = fields.Char(string='Description')
    text = fields.Html(string='Text')

    ###########################################################################
    # Model methods
    ###########################################################################
