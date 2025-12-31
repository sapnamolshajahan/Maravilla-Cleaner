# -*- coding: utf-8 -*-
import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BulkCustomerDispatch(models.TransientModel):
    """
    Bulk Customer Invoice Dispatch
    """
    _name = "bulk.customer.invoice.dispatch"
    _description = __doc__

    ###########################################################################
    # Fields
    ###########################################################################
    from_date = fields.Date("From Date", required=True, default=fields.Date.today())
    ignore_sent = fields.Boolean("Ignore Invoice Sent Date")
    include_credits = fields.Boolean("Include Credit Notes", default=True)
    all_customers = fields.Boolean("All Customers", default=True)
    lines = fields.One2many("bulk.customer.invoice.line", "header", string="Customers")

    def build_wizard(self, partners):
        """
        :param partners: iterable res.partner records
        :return:
        """
        lines = []
        for p in partners:
            if not p.customer_rank:
                raise UserError("'{}' is not a Customer".format(p.name))
            lines.append((0, 0, {"partner": p.id}))

        return self.create(
            [{
                "all_customers": not partners,
                "lines": lines,
            }])

    def button_generate(self):

        invoices = self._find_invoices()
        _logger.debug("{0} invoices found".format(len(invoices)))
        self._send_invoices(invoices)

        return True

    def _find_invoices(self):

        domain = [
            ("state", "=", "posted"),
            ("invoice_date", ">=", self.from_date),
        ]
        if self.include_credits:
            domain.append(("move_type", "in", ["out_invoice", "out_refund"]))
        else:
            domain.append(("move_type", "=", "out_invoice"))
        if not self.ignore_sent:
            domain.append(("is_move_sent", "!=", True))
        if not self.all_customers:
            customer_ids = [x.partner.id for x in self.lines]
            domain.append(("partner_id", "in", customer_ids))

        return self.env["account.move"].search(domain)

    def _send_invoices(self, invoices):
        for inv in invoices:
            if inv.move_type == "out_refund":
                doc_type = "credit-note"
            else:
                doc_type = "invoice"
            self.env["email.async.send"].force_send(doc_type, [inv.id], inv.partner_id, "email_invoice_sent")
            lock_date = inv.company_id._get_user_fiscal_lock_date(invoices.journal_id)
            if inv.date > lock_date:
                inv.write({'sent': True})


class BulkCustomerDispatchLine(models.TransientModel):
    _name = "bulk.customer.invoice.line"
    _description = "Bulk Customer Invoice Dispatch Line"

    ################################################################################
    # Fields
    ################################################################################
    header = fields.Many2one("bulk.customer.invoice.dispatch", required=True, ondelete="cascade")
    partner = fields.Many2one("res.partner", string="Customer", required=True, ondelete="cascade")
