# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    team_id = fields.Many2one(
        'crm.team', string='Sales Team',
        compute='_compute_team_id',
        precompute=True,  # avoid queries post-create
        ondelete='set null', readonly=False, store=True)

    @api.depends('parent_id')
    def _compute_team_id(self):
        for partner in self.filtered(
                lambda partner: not partner.team_id and partner.company_type == 'person' and partner.parent_id.team_id):
            partner.team_id = partner.parent_id.team_id

