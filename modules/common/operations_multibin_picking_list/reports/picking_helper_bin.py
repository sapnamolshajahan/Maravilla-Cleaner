# -*- coding: utf-8 -*-
from odoo.addons.operations_picking_list_reports.reports.picking_helper import PickingHelper


class PickingListHelper(PickingHelper):

    def move(self, move_id):
        move = self.env["stock.move"].browse(move_id)
        result = super(PickingListHelper, self).move(move_id)
        result['bin'] = move.bin_id.name if move.bin_id else ""
        return result
