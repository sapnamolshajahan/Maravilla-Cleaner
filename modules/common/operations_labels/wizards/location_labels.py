# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LocationLabels(models.TransientModel):
    """
    Print Labels for Stock Locations
    """
    _name = "operations.labels.location.wizard"
    _description = __doc__.strip()

    ################################################################################
    # Fields
    ################################################################################
    printer = fields.Many2one("label.printer")
    queue = fields.Char(related="printer.queue")
    label = fields.Many2one("label.printer.template")
    lines = fields.One2many("operations.labels.location.wizard.line", "wizard")
    barcoded_only = fields.Boolean("Barcoded Locations Only", default=True)

    ################################################################################
    # Technical Fields
    ################################################################################
    def default_get(self, fields_list):

        result = super().default_get(fields_list)

        # default in the printer, if there are any
        for printer in self.env["label.printer"].search([]):
            result["printer"] = printer.id
            break

        # Populate label template field if possible
        labels = self.env["label.printer.template"].search(
            [
                ("state", "=", "a-active"),
                ("model", "=", "stock.location"),
            ])
        for label in labels:
            result["label"] = label.id
            break

        return result

    ################################################################################
    # Business Methods
    ################################################################################
    @api.model
    def create_wizard(self, locations):
        return self.create(
            [{
                "lines": [
                    (0, 0,
                     {
                         "location": l.id,
                     }) for l in locations
                ],
            }])

    def action_print(self):

        for line in self.lines:
            if not self.barcoded_only or line.barcode:
                self.label.print_to_queue(line.location, self.queue)

        return {"type": "ir.actions.act_window_close"}


class LocationLabelLines(models.TransientModel):
    """
    Lines with Locations to Print
    """
    _name = "operations.labels.location.wizard.line"
    _description = __doc__.strip()

    ################################################################################
    # Fields
    ################################################################################
    wizard = fields.Many2one("operations.labels.location.wizard", required=True, ondelete="cascade")
    location = fields.Many2one("stock.location", required=True)
    barcode = fields.Char(related="location.barcode")
