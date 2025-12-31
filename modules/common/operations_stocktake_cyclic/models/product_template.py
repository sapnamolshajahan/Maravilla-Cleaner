from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cyclic_count_frequency = fields.Many2one('product.cyclic.count', string='Cyclic Count Frequency')
    last_count_date = fields.Date()


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    incl_cyclic = fields.Boolean(string='Include for Cyclic Counts')


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    cyclic = fields.Boolean(string='Cyclic')