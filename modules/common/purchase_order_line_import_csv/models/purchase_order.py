# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_import_purchase_order_lines(self):
        """
        Trigger the purchase order line import.

        Returns:
            A window action to display the line import wizard.
        """
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Purchase Line import only available for Draft state Purchase Orders")

        wizard = self.env["purchase.order.line.import"].create({"purchase": self.id})
        return {
            "name": "Import Purchase Order Lines",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": self.env.context
        }

    def action_set_purchase_order_value(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError("You can only set the Purchase Order value when it's state is draft. ")

        wizard = self.env["purchase.purchase_order_value"].create(
            {
                "purchase": self.id,
                "value": self.amount_untaxed,
            })

        return {
            "name": "Set Purchase Order Value",
            "view_mode": "form",
            "view_id": False,
            "view_type": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }
