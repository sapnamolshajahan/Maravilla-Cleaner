# -*- coding: utf-8 -*-
import base64
import logging

from odoo import models, fields, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ChoosePartner(models.TransientModel):
    _name = "remittance.advice.choose.partner"
    _description = 'Remittance Advice Choose Partner'

    ###########################################################################
    # Fields
    ###########################################################################
    payment_list = fields.Char(string="List of Payments")
    lines = fields.One2many("remittance.advice.choose.partner.line", inverse_name="header", string="Partner List")

    ###########################################################################
    # Business Methods
    ###########################################################################
    def from_email(self):
        return self.env.company.account_email_address or self.env.user.email

    def print_reports(self):
        self.ensure_one()

        payment_ids = eval(self.payment_list)
        partner_ids = []
        for line in self.lines:
            if line.print_it:
                partner_ids.append(line.partner_id.id)

        if not partner_ids:
            raise UserError("Please add one or more batches")

        report = self.env["account.payment"].get_remittance_report()

        data = {
            "ids": payment_ids,  # Force viaduct to use payment ids
            "viaduct-parameters": {
                "all-partners": False,
                "partner-ids": partner_ids,
            }
        }

        # Re-Force active_ids
        context = dict(self.env.context)
        context["active_ids"] = partner_ids

        payment = self.env["account.payment"].browse(payment_ids[0])
        payment = str(payment.name)
        filename = "Remittance Advice - " + payment

        return {
            "name": filename,
            "type": "ir.actions.report",
            "report_name": report.report_name,
            "report_type": report.report_type,
            "report_file": report.report_file,
            "data": data,
            "context": context
        }

    def email_reports(self):
        self.ensure_one()
        wizard = self
        payment_ids = eval(wizard.payment_list)
        partner_print_ids = list(set([line.partner_id.id for line in wizard.lines if line.print_it]))

        for payment in self.env["account.payment"].browse(payment_ids):
            for partner in self.env["res.partner"].browse(partner_print_ids):

                if not partner.email:
                    _logger.info("remittance advice not sent, no email address for {}".format(partner.display_name))
                    continue

                if payment.partner_id.id != partner.id:
                    continue

                report_data = {
                    "viaduct-parameters": {
                        "all-partners": False,
                        "partner-ids": [partner.id],
                    }
                }

                report = payment.get_remittance_report()
                data, _ = self.env["ir.actions.report"]._render(report, [payment.id], report_data)

                attach = self.env["ir.attachment"].create(
                    {
                        "name": "Remittance Advice - {0}.pdf".format(payment.name),
                        "mimetype": "application/octet-stream",
                        "datas": base64.b64encode(data),
                    })
                from_email = self.from_email()
                body = tools.plaintext2html("Remittance Advice {0} attached".format(payment.name))

                email = self.env["mail.mail"].create(
                    {
                        "email_to": partner.email,
                        "email_from": from_email,
                        "reply_to": from_email,
                        "subject": "Remittance Advice {0} from {1}".format(payment.name, payment.company_id.name),
                        "body_html": body,
                        "attachment_ids": [(6, 0, attach.ids)],
                    })
                attach.write(
                    {
                        "res_model": email._name,
                        "res_id": email.id,
                    })

                _logger.debug(f"payment_remittance_advise: created mail: {email.id} for partner: {partner.name}")

        return True


class ChoosePartnerLine(models.TransientModel):
    _name = "remittance.advice.choose.partner.line"
    _description = 'Remittance Advice Choose Partner Line'

    ###########################################################################
    # Fields
    ###########################################################################
    header = fields.Many2one("remittance.advice.choose.partner", readonly=True, required=True, ondelete="cascade")
    print_it = fields.Boolean(string="Print this Partner", default=True)
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    email = fields.Char(string="Email", readonly=True, size=128)
