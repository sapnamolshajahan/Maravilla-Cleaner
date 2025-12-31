# -*- coding: utf-8 -*-
from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    def _compute_activity_count(self):
        for partner in self:
            partner.activity_count = 0

    ################################################################################
    # Fields
    ################################################################################
    activity_count = fields.Integer("Activity", compute="_compute_activity_count")
    rating = fields.Many2one(comodel_name='res.partner.rating', string='Rating')
    lead_contact_sequence = fields.Integer("Lead Contact Sequence", default=20)
    mobile = fields.Char()


class PartnerRating(models.Model):
    _name = 'res.partner.rating'
    _description = 'Partner Rating'

    name = fields.Char(string='Description')
