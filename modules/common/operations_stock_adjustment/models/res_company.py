from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    adjustment_approver = fields.Many2one('res.users', string="Adjustment Approver")
