# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def get_invoice_report(self):
        """
        Return the the report to use.

        This can be overidden to provide customised reports.
        :return: ir.actions.report record
        """
        return self.env.ref("account_basic_invoice_reports.basic_invoice_viaduct")

    def get_printed_report_name(self):
        """
        Used in reports.xml.

        :return: Save-able name for the report, avoid '/' characters; can be overridden.
        """
        if self.name:
            return self.name.replace("/", "-")
        else:
            return 'Draft'

    @api.model
    def get_sendout_email_template(self):
        """
        mail.template record to use for email send-out

        :return: mail.template reference
        """
        return self.env.ref("account.email_template_edi_invoice")

    def action_send_and_print_context(self, template):
        """
        Set context for action_send_and_print().

        Override as required.

        :param template:
        :return: context dictionary.
        """
        result = dict(self.env.context)
        result.update(
            {
                "active_ids": self.ids,
                "default_mail_template_id": template and template.id or False,
            })
        return result

    def action_send_and_print(self):
        """
        Override the base-version to introduce:
            * get_sendout_email_template()
            * get_invoice_report()
            * action_invoice_sent_context() to allow overrides
        """
        # self.ensure_one()
        for record in self:
            template = record.get_sendout_email_template()

            if any(not x.is_sale_document(include_receipts=True) for x in record):
                raise UserError("You can only send sales documents")

            report = record.get_invoice_report()
            if not template.report_template_ids or template.report_template_ids[0] != report:
                template.write({"report_template_ids": [(6, 0, [report.id])]})

            return {
                "name": "Send",
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "account.move.send.wizard",
                "target": "new",
                "context": record.action_send_and_print_context(template),
            }

    def action_print_pdf(self):
        self.ensure_one()
        report = self.get_invoice_report()
        return report.report_action(self.id)
