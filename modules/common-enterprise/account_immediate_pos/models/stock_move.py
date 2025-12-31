from odoo import fields, models, api
import pytz


class StockMove(models.Model):
    _inherit = 'stock.move'

    pos_order_line = fields.Many2one('pos.order.line', string='POS Order Line')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        res_dict = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        res_dict['pos_order_line'] = first_line.id
        return res_dict
