# -*- coding: utf-8 -*-

from operator import attrgetter

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ###########################################################################
    # model methods.
    ###########################################################################
    def sequence_moves(self):
        for picking in self:
            binned_moves = []
            unbinned_moves = []
            other_moves = []

            for move in picking.move_ids:
                if move.bin_id:
                    binned_moves.append(move)
                elif move.product_id.default_code:
                    unbinned_moves.append(move)
                else:
                    other_moves.append(move)
            moves = [x for x in sorted(binned_moves, key=attrgetter("bin_id.name"))]
            moves.extend([x for x in sorted(unbinned_moves, key=attrgetter("product_id.default_code"))])
            moves.extend([x for x in sorted(other_moves, key=attrgetter("product_id.name"))])
            for seq, move in enumerate(moves):
                move.write({"pick_list_sequence": seq})

    def action_assign(self):
        """
        Add sequencing for the moves on the picking list.
        """
        result = super(StockPicking, self).action_assign()
        for picking in self:
            if all([x == 0 for x in picking.mapped('move_ids.pick_list_sequence')]):
                picking.sequence_moves()

        return result

    def action_confirm(self):
        """
        Add sequencing for the moves on the picking list.
        """
        result = super(StockPicking, self).action_confirm()
        for picking in self:
            if all([x == 0 for x in picking.mapped('move_ids.pick_list_sequence')]):
                picking.sequence_moves()

        return result

    def action_detailed_operations(self):
        self.ensure_one()
        res = super().action_detailed_operations()
        stock = self.env['stock.move']
        res['context']['default_order'] = stock.pick_list_sequence
        return res

