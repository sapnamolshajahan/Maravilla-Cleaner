from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_intermediate = fields.Boolean(related="product_tmpl_id.is_intermediate")
