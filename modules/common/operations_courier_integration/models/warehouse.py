# -*- coding: utf-8 -*-
from odoo import fields, models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    ################################################################################
    # Fields
    ################################################################################
    carrier_label_printer_ids = fields.One2many("carrier.label.printer", "warehouse_id", "Label Printers",
                                                help="Label Printer Queues used for carrier labels")

    ################################################################################
    # Methods
    ################################################################################
    def default_printer(self):
        """
        :return: default printer, or the first one in the list.
        """
        self.ensure_one()
        printers = self.carrier_label_printer_ids.filtered(lambda r: r.default)
        if not printers:
            printers = self.carrier_label_printer_ids
        for p in printers:
            return p
        return None
