from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qty_uplift = fields.Float(
        string="Default Qty Uplift",
        related='company_id.qty_uplift',
        readonly=False,
        help="Default percentage increase to apply to Momentus event quantities."
    )
