# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ################################################################################
    # Business Methods
    ################################################################################
    def action_print_labels(self):
        label = self.env["label.printer.template"].search(
            [
                ("state", "=", "a-active"),
                ("model", "=", self._name),
            ], limit=1)
        if not label:
            raise UserError("No active labels defined for Product Template")

        wizard = self.env["operations.labels.product.wizard"].create({'product_tmpl_ids': self, 'label': label.id})
        return {
            "name": wizard._description,
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "context": self.env.context,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def action_open_label_layout(self):
        """
        Replace method with our custom method.
        :return:
        """
        return self.action_print_labels()
