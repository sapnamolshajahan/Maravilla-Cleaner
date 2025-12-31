# -*- coding: utf-8 -*-
import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BulkDispatch(models.TransientModel):
    """
    Bulk Invoice Dispatch
    """
    _name = "bulk.invoice.dispatch"
    _description = __doc__

    ###########################################################################
    # Fields
    ###########################################################################
    lines = fields.One2many("bulk.invoice.dispatch.line", "header", string="Customers")

    ###########################################################################
    # Methods
    ###########################################################################
    def build_wizard(self, invoices):
        """
        :param partners: iterable account.move records
        :return:
        """
        lines = []
        for move in invoices:
            if move.move_type not in ("out_invoice", "out_refund"):
                raise UserError(f"{move.name} is not a Invoice or Credit Note")
            lines.append((0, 0, {"invoice": move.id}))

        return self.create(
            [{
                "lines": lines,
            }])

    def button_generate(self):

        self._send_invoices(self.lines.invoice)

        return True

    def _send_invoices(self, invoices):
        journal = invoices.journal_id
        lock_date = self.env.company._get_user_fiscal_lock_date(journal)
        for inv in invoices:
            if inv.move_type == "out_refund":
                doc_type = "credit-note"
            else:
                doc_type = "invoice"
            self.env["email.async.send"].force_send(doc_type, [inv.id], inv.partner_id, "email_invoice_sent")
            if inv.date > lock_date:
                inv.write({'sent': True})


class BulkDispatchLine(models.TransientModel):
    _name = "bulk.invoice.dispatch.line"
    _description = 'Bulk Invoice Dispatch Line'

    ################################################################################
    # Fields
    ################################################################################
    header = fields.Many2one("bulk.invoice.dispatch", required=True, ondelete="cascade")
    invoice = fields.Many2one("account.move", string="Invoice/Credit", required=True, ondelete="cascade")
    partner = fields.Many2one("res.partner", related="invoice.partner_id")
