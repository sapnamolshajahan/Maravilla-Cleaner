# -*- coding: utf-8 -*-
from odoo import fields, models, api


class FleetStockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends("price_unit", "product_uom_qty")
    def _calc_extended_cost(self):
        for rec in self:
            rec.extended_cost = rec.price_unit * rec.product_uom_qty

    ##################################
    # fields
    ##################################
    fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")
    extended_cost = fields.Float(compute="_calc_extended_cost", string="Extended Cost", digits="Accounting")


class FleetStockPicking(models.Model):
    _inherit = 'stock.picking'

    fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")

    # def do_recompute_remaining_quantities(self, done_qtys=False):
    #     """ This function seems to be not useful"""
    #
    #     super(FleetStockPicking, self).do_recompute_remaining_quantities(done_qtys)
    #     for picking in self:
    #         for move in picking.move_lines:
    #             if move.purchase_line_id and move.purchase_line_id.fleet_id:
    #                 move_operation_ids = self.env['stock.move.operation.link'].search([('move_id', '=', move.id)])
    #                 if move_operation_ids:
    #                     for operation in move_operation_ids:
    #                         stock_pack_operation_id = operation.operation_id
    #                         if not stock_pack_operation_id.done_by_user:
    #                             stock_pack_operation_id.write({'fleet_id': move.purchase_line_id.fleet_id.id})
