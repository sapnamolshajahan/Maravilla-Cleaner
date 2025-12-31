from odoo import fields, models

class ProductProduct(models.Model):
    _inherit = "product.product"

    normal_buy_price_json = fields.Json(string="Normal Buy Price (per company)")
