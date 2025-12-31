from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    use_description = fields.Boolean(string="Use Product Description from Momentus")
    return_category = fields.Boolean(string="Return Category",
                                     help="If checked, products in this category are expected to be returned after the event.")
