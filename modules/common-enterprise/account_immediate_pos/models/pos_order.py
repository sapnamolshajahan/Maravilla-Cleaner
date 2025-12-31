from odoo import fields, models, api
from itertools import groupby


class POSOrder(models.Model):
    _inherit = 'pos.order'

    pos_order_line = fields.Many2one('pos.order.line', string='POS Order Line')


class POSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def _launch_stock_rule_from_pos_order_lines(self):
        res = super(POSOrderLine, self)._launch_stock_rule_from_pos_order_lines()
        orders = self.mapped('order_id')
        for order in orders:
            for picking in order.picking_ids:
                tracked_lines = order.lines
                lines_by_tracked_product = groupby(sorted(tracked_lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
                for product_id, lines in lines_by_tracked_product:
                    lines = self.env['pos.order.line'].concat(*lines)
                    moves = picking.move_ids.filtered(lambda m: m.product_id.id == product_id)
                    for move in moves:
                        move.write({
                        'pos_order_line': lines[0].id,
                        'value': move.product_uom_qty * move.product_id.standard_price})

        return res
