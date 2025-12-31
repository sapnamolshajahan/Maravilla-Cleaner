# -*- coding: utf-8 -*-
import base64
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def print_pos_auto(self):
        """
        Autoprint receipt and invoice if configured.

        This method is intended to be invoked directly from the front-end.
        """
        self.filtered(lambda p: p.config_id.autoprint_receipt).print_pos_receipt()
        self.filtered(lambda p: p.config_id.autoprint_invoice).print_pos_invoice()

    def print_pos_invoice(self):
        """
        Print the invoice associated with the POS Order.
        """
        for pos_order in self:
            queue = pos_order.config_id.pos_invoice_queue
            if not queue:
                _logger.debug(f"ignored pos={pos_order.name}, no invoice queue config={pos_order.config_id.name}")
                continue

            self.with_delay(
                channel=self.light_job_channel(),
                description=f"POS Invoice Print: {pos_order.name}",
            )._print_pos_invoice_job(pos_order.id, queue)

    @api.model
    def _print_pos_invoice_job(self, order_id, queue):
        """
        Queue Job entry point.

        Print an invoice for a POS Order.

        :param order_id:
        :param queue: printer queue
        """
        pos_order = self.browse(order_id)
        invoice = pos_order.account_move
        report = invoice.get_invoice_report()
        result, _format = report._render(report, [invoice.id])
        if not self.lp_command(queue, result):
            _logger.warning(f"failed print: invoice={invoice.name}, report={report.name}, queue={queue}")

    def action_receipt_to_customer(self, name, client, ticket):
        """
        Email the Invoice (and not the receipt) to the Customer.

        :param name:
        :param client:
        :param ticket:
        :return:
        """
        if not self:
            return False
        if not client.get("email"):
            return False

        message = f"<p>Dear {client['name']},<br/>Here is your electronic ticket for {name}. </p>"
        mail_values = {
            "subject": f"Receipt {name}",
            "body_html": message,
            "author_id": self.env.user.partner_id.id,
            "email_from": self.env.company.email or self.env.user.email_formatted,
            "email_to": client["email"],
        }

        if self.account_move:
            report = self.account_move.get_invoice_report()
            data, _fmt = report._render(report, [self.account_move.id])
            filename = name + ".pdf"
            attachment = self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "type": "binary",
                    "datas": base64.b64encode(data),
                    "store_fname": filename,
                    "res_model": "pos.order",
                    "res_id": self.ids[0],
                    "mimetype": "application/x-pdf"
                })
            mail_values["attachment_ids"] = [(4, attachment.id)]

        mail = self.env["mail.mail"].sudo().create(mail_values)
        mail.send()
