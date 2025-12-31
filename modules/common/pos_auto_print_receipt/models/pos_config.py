# -*- coding: utf-8 -*-
from odoo import models, fields


class POSConfig(models.Model):
    _inherit = "pos.config"

    ################################################################################
    # Fields
    ################################################################################
    autoprint_receipt = fields.Boolean(string="Autoprint POS Receipt", default=True)
    autoprint_invoice = fields.Boolean(string="Autoprint Invoice", default=True)
    pos_invoice_queue = fields.Char(string="POS Invoice Queue")

    ################################################################################
    # Business Methods
    ################################################################################
    def open_cashbox(self):
        """
        Open the cashbox connected to the Receipt Printer.

        :return:
        """
        self.ensure_one()
        if self.pos_receipt_queue:
            self.env.ref("pos_auto_print_receipt.open_cashbox").print_to_queue(self, self.pos_receipt_queue.name)
