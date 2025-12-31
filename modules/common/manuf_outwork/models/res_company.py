# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    aggregate_po = fields.Boolean(string='Add new outwork to existing draft PO')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    aggregate_po = fields.Boolean(string='Add new outwork to existing draft PO',
                                        default=lambda self: self.env.company.aggregate_po)

    @api.onchange('aggregate_po')
    def onchange_aggregate_po(self):
        if self.aggregate_po:
            self.env.company.write({'aggregate_po': True})
        else:
            self.env.company.write({'aggregate_po': False})




