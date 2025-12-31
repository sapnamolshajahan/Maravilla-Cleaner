from odoo import models, fields, api, _


class ProductHoldMenu(models.Model):
    _name = 'product.hold'
    _description = 'Products On Hold'
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Char(string="Quantity", required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    hold_to_date = fields.Date(string="Hold To Date", required=True)

