from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.template'

    momentus_resource_code = fields.Char(
        string="Momentus Resource Code",
        help="Unique resource code from Momentus used for product matching.",
        index=True
    )
