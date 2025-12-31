# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_import_transfers(self):
        self.ensure_one()

        if self.picking_type_id.code != "internal":
            raise UserError("Only for internal transfers")
        if self.state != "draft":
            raise UserError("Can only import when transfer is in draft state")

        wizard = self.env["import.transfers.csv"].create(
            {
                "picking": self.id,
                "source_location_id": self.location_id.id,
                "dest_location_id": self.location_dest_id.id,
            })
        return {
            "name": "Import Lines from Excel",
            "view_mode": "form",
            "view_id": False,
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
