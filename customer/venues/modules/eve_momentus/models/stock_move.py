from odoo import models, fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    eve_event = fields.Many2one('eve.event', string="Momentus Event")
    momentus_wo = fields.Integer(string="Momentus Work Order")