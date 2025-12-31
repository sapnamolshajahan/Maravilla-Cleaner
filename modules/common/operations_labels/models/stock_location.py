# -*- coding: utf-8 -*-
from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    ################################################################################
    # Business Methods
    ################################################################################
    def action_location_labels(self):
        wizard = self.env["operations.labels.location.wizard"].create_wizard(self)
        return {
            "name": wizard._description,
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "context": self.env.context,
            "type": "ir.actions.act_window",
            "target": "new",
        }
