# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = "stock.move"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    @api.depends('location_id')
    def _bin_id(self):
        for rec in self:
            wbin_model = rec.env["stock.warehouse.bin"]
            if rec.picking_id.picking_type_id.code == "incoming":
                if rec.location_dest_id.warehouses:
                    wbins = wbin_model.search(
                        [
                            ("product_id", "=", rec.product_id.id),
                            ("warehouse_id", "=", rec.location_dest_id.warehouses[0].id),
                        ], order="id ASC", limit=1)

                    if wbins:
                        rec.bin_id = wbins[0]
                    else:
                        rec.bin_id = None

            else:
                if rec.location_id.warehouses:
                    wbins = wbin_model.search(
                        [
                            ("product_id", "=", rec.product_id.id),
                            ("warehouse_id", "=", rec.location_id.warehouses[0].id),
                        ], order="id ASC", limit=1)

                    if wbins:
                        rec.bin_id = wbins[0]
                    else:
                        rec.bin_id = None


    ###########################################################################
    # Fields
    ###########################################################################

    pick_list_sequence = fields.Integer(string="Display Sequence for picking list")
    bin_id = fields.Many2one(comodel_name="stock.warehouse.bin", string="Bin",
                             compute="_bin_id", store=True, readonly=True)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    bin_id = fields.Many2one("stock.warehouse.bin", string="Bin",
                             related="move_id.bin_id", store=True)
