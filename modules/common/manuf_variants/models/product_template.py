from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_intermediate = fields.Boolean(default=False)
