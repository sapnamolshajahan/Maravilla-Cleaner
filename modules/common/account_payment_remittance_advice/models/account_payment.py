# -*- coding: utf-8 -*-
import logging

from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    ######################################################################################
    # Fields
    ######################################################################################
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company.id, required=True)

    ######################################################################################
    # Methods
    ######################################################################################
    @api.model
    def get_remittance_report(self):
        """
        Override to use customised report.
        """
        return self.env.ref("account_payment_remittance_advice.payment_remittance_advice")

    def remittance_order_print(self):

        report_data = {
            "viaduct-parameters": {
                "all-partners": True,  # disable partner-filter on report
                "partner-ids": [],
            }
        }

        report = self.get_remittance_report()
        return {
            "name": "Remittance Advice",
            "type": "ir.actions.report",
            "report_name": report.report_name,
            "report_type": report.report_type,
            "data": report_data,
            "context": self.env.context
        }

    def action_email_remittance_order(self):

        if not self.env.context.get("active_ids", None):
            raise UserError("No payments selected")

        partner_set = set()
        for payment_order in self.browse(self.env.context["active_ids"]):
            partner_set.update([x.partner_id.id for x in payment_order])

        lines = []
        for partner in self.env["res.partner"].browse(list(partner_set)):
            lines.append((0, 0,
                          {
                              "partner_id": partner.id,
                              "email": partner.email,
                              "print_it": True if partner.email else False,
                          }))

        wizard = self.env["remittance.advice.choose.partner"].create(
            {
                "payment_list": str(self.env.context["active_ids"]),
                "lines": lines,
            })

        return {
            "name": "Email/Print Remittance Advice",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
        }
