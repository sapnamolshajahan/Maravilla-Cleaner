# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ##################################################################################
    # Fields
    ##################################################################################
    validity_date = fields.Date(readonly=False)  # Override base to allow modification

    def get_sale_report(self):
        """
        Override as required to provide customised reports.
        """
        return self.env.ref("sale_order_reports.generic_sale_viaduct")

    def get_printed_object_name(self):
        return self.name

    def get_printed_report_name(self):
        prefix = "Sale" if self.state in ("sale", "done") else "Quotation"
        return f"{prefix} - {self.name.replace('/', '-')}"

    def button_print_report(self):
        report = self.get_sale_report()
        # return report.report_action(self.id)
        return {
            "type": "ir.actions.report",
            "report_name": report.report_name,
            "report_type": report.report_type,
            "report_file": report.report_file,
            "context": dict(self.env.context, active_ids=[self.id]),
        }

    def get_proforma_email_template(self):
        """
        Email template to use for proforma email.

        Using a local proforma email-template allows us the option to define
        custom pro-forma reports that can be attached to it, without affecting
        the main sale-confirmation email-template.
        :return:
        """
        return self.env.ref("sale_order_reports.email_template_proforma")

    def _find_mail_template(self):
        """
        Override to allow use of local proforma email template.

        :param force_confirmation_template:
        :return:
        """
        if self.env.context.get("proforma", False):
            return self.get_proforma_email_template()
        return super(SaleOrder, self)._find_mail_template()

    def action_quotation_send_context(self, template, lang):
        """
        Set context for action_quotation_send().

        Override as required.

        :param template:
        :param lang:
        :return: context dictionary.
        """
        return {
            "default_model": "sale.order",
            "default_res_ids": self.ids,
            "default_use_template": bool(template.id),
            "default_template_id": template.id,
            "default_composition_mode": "comment",
            "mark_so_as_sent": True,
            # "custom_layout": "mail.mail_notification_paynow",
            "proforma": self.env.context.get("proforma", False),
            "force_email": True,
            "model_description": self.with_context(lang=lang).type_name,
        }

    def action_quotation_send(self):
        """
        Override base version.

        This version uses action_quotation_send_context() to
        allow custom context overrides.
        """
        self.ensure_one()
        template = self._find_mail_template()
        lang = self.env.context.get('lang')

        if template.lang:
            lang = template._render_lang(self.ids)[self.id]

        report = self.get_sale_report()
        if not template.report_template_ids or report.id not in template.report_template_ids.ids:
            # Force the template to use the installation's report instead.
            template.write({"report_template_ids": [(4, report.id)]})

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': self.action_quotation_send_context(template, lang),
        }
