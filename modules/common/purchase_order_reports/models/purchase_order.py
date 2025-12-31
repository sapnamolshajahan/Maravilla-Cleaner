# -*- coding: utf-8 -*-
from odoo import api, models

CONTEXT_EMAIL_PRICED = "purchase_order_reports.priced_email"


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _set_priced_context(self, priced):
        """
        Add priced/unpriced value to context
        """
        context = dict(self.env.context)
        context[CONTEXT_EMAIL_PRICED] = priced
        return context

    def _review_email(self, priced):
        """
        Bring up the mail-thread review, if configured.

        :param priced: priced/unpriced report in email..
        """
        context = self._set_priced_context(priced)
        if self.company_id.purchase_report_email_review:
            return self.with_context(context).action_rfq_send()

        template = self.get_email_template(self.purchase_order_report())
        template.with_context(context).send_mail(self.id, force_send=True)
        return True

    def button_approve(self, force=False):
        """
        Override to email out purchase orders, if enabled.
        """
        # TODO: Add code to email on approval
        return super(PurchaseOrder, self).button_approve(force)

    @api.model
    def purchase_order_report(self):
        """
        Override for customised versions
        """
        return self.env.ref("purchase_order_reports.generic_purchase_viaduct")

    def print_quotation(self):
        """
        Override to allow custom reports to be used.
        """
        self.write({'state': "sent"})

        context = self._set_priced_context(self.partner_id.purchase_report_pricing == "priced")
        return self.purchase_order_report().with_context(context).report_action(self)

    def button_print_report(self):
        """
        Show the wizard for printing.
        """
        if self.partner_id.purchase_report_pricing == "ask":
            return self.get_report_wizard("print")

        context = self._set_priced_context(self.partner_id.purchase_report_pricing == "priced")
        return self.purchase_order_report().with_context(context).report_action(self)

    def button_send_by_email(self):
        """
        Show the wizard for printing.
        """
        if self.partner_id.purchase_report_pricing == "ask":
            return self.get_report_wizard("email")
        return self._review_email(self.partner_id.purchase_report_pricing == "priced")

    def get_report_wizard(self, action_type):
        """
        Create the wizard and return the action to display it.

        :param action_type: print or email.
        :eturns: the appropriate action.
        """
        wizard = self.env["purchase.order.report.wizard"].create_wizard(self, action_type)
        return {
            "name": "Purchase Order Report Type",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "target": "new"
        }

    @api.model
    def email_compose_form(self):
        return self.env.ref("mail.email_compose_message_wizard_form")

    @api.model
    def get_email_template(self, report):
        """
        Inspect context for the right email template to use.
        """
        if self.env.context.get("send_rfq", False):
            template = self.rfq_email_template()
        else:
            template = self.purchase_email_template()

        if not template.report_template_ids or report.id not in template.report_template_ids.ids:
            # Force the template to use the installation's report instead.
            template.write({"report_template_ids": [(4, report.id)]})

        return template

    @api.model
    def rfq_email_template(self):
        return self.env.ref("purchase.email_template_edi_purchase")

    @api.model
    def purchase_email_template(self):
        return self.env.ref("purchase.email_template_edi_purchase_done")

    def action_rfq_send(self):
        """
        Replace the base-version with one that
        * allows email-template overrides
        * allows custom reports via purchase_order_report()
        * allows custom contexts via action_rfq_send_context()
        """
        self.ensure_one()
        report = self.purchase_order_report()
        template = self.get_email_template(report)
        compose_form = self.email_compose_form()

        lang = self.env.context.get("lang")
        ctx = self.action_rfq_send_context(template, lang)
        if {"default_template_id", "default_model", "default_res_ids"} <= ctx.keys():
            if template and template.lang:
                lang = template._render_lang([ctx["default_res_ids"]])[ctx["default_res_ids"]]

        return {
            "name": "Compose Email",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def action_rfq_send_context(self, template, lang):
        """
        Provide context for use with the email compose-form.
        """
        context = dict(self.env.context)
        if self.state in ["draft", "sent"]:
            description = "Request for Quotation"
        else:
            description = "Purchase Order"
        context.update(
            {
                "default_model": "purchase.order",
                "active_model": "purchase.order",
                "active_id": self.ids[0],
                "default_use_template": True,
                "default_template_id": template.id,
                "default_composition_mode": "comment",
                "default_email_layout_xmlid": "mail.mail_notification_layout_with_responsible_signature",
                "force_email": True,
                "mark_rfq_as_sent": True,
                "model_description": description,
            })
        return context
