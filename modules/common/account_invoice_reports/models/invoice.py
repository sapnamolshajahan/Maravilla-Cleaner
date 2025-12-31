# -*- coding: utf-8 -*-
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def get_invoice_report(self):
        """
        Override to use this module's report

        :return: ir.actions.report record
        """
        return self.env.ref("account_invoice_reports.standard_invoice_viaduct")

    @api.model
    def get_journal_report(self):
        """
        This can be overidden to provide customised reports.

        :return: ir.actions.report record
        """
        return self.env.ref("account_invoice_reports.standard_journal_viaduct")
