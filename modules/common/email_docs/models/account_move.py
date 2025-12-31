# -*- coding: utf-8 -*-
import logging
from markupsafe import Markup
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class InvoiceEmailDocs(models.Model):
    _inherit = "account.move"

    sent = fields.Boolean(readonly=False, string='Emailed')

    def action_post(self):
        """
        Trigger the async email send at the end of the invoice workflow.
        """
        res = super(InvoiceEmailDocs, self).action_post()

        for record in self:
            doc_type = record.get_email_doc_type()
            if doc_type:
                self.env["email.async.send"].send(doc_type, record.id, record.partner_id.id, "email_invoice_sent")
        return res

    def get_email_doc_type(self):
        """Place doct type selection in a separate function so it can be modified in customer-specific modules"""
        if self.move_type == "out_invoice":
            return "invoice"
        elif self.move_type == "out_refund":
            return "credit-note"

    @api.model
    def email_doc_report(self):
        """
        Return the report-name to use for Invoices and Credit Notes.

        Override to provide customer-specific report-names.

        :return: ir.actions.report record
        """
        return self.get_invoice_report()

    def email_invoice_sent(self):
        """
        Standard Callback after invoices has been sent.
        """
        self.write({"is_move_sent": True})

    def action_bulk_invoice_wizard(self):
        """
        Bring up the Bulk Invoice wizard with the selected invoices.
        :return:
        """
        wizard = self.env["bulk.invoice.dispatch"].build_wizard(self)
        return {
            "name": wizard._description,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "target": "new",
        }

    def action_send_and_print(self):
        for rec in self:
            rec.write({'sent': True})
        return super(InvoiceEmailDocs, self).action_send_and_print()

