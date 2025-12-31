from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    qty_uplift = fields.Float(string="Default Qty Uplift")