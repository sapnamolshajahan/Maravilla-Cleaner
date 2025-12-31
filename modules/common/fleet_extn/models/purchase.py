# -*- coding: utf-8 -*-
from odoo import fields, models


class FleetPurchaseLine(models.Model):
    _inherit = 'purchase.order.line'

    fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")

    def _create_stock_moves(self, picking):
        done = super(FleetPurchaseLine, self)._create_stock_moves(picking)
        for move in done:
            if move.purchase_line_id and move.purchase_line_id.fleet_id:
                move.write({'fleet_id': move.purchase_line_id.fleet_id.id})

        return done
