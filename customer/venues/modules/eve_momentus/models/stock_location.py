from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    momentus_space_code = fields.Char(
        string="Momentus Space Code",
        help="Space code from Momentus used to map destination locations.",
        index=True
    )
