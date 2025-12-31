# -*- coding: utf-8 -*-
from odoo import fields, models
from ..models.company import PURCHASE_PRINT_BASE_OPTIONS


class PurchaseOrderReport(models.TransientModel):
    """
    Type of Purchase Order Report to Produce
    """
    _name = "purchase.order.report.wizard"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################
    purchase_order = fields.Many2one("purchase.order", string="Purchase Order",
                                     required=True, readonly=True, ondelete="cascade")
    action_type = fields.Selection(
        [
            ("email", "Email"),
            ("print", "Print")
        ], string="Action Type", required=True)
    report_pricing = fields.Selection(PURCHASE_PRINT_BASE_OPTIONS, string="Report Pricing", required=True)

    ################################################################################
    # Business Methods
    ################################################################################
    def create_wizard(self, purchase, action):
        pricing = purchase.partner_id.purchase_report_pricing
        if pricing == "ask":
            pricing = "priced"
        return self.create(
            [
                {
                    "purchase_order": purchase.id,
                    "action_type": action,
                    "report_pricing": pricing,
                }
            ])

    def email_report(self):
        self.ensure_one()
        return self.purchase_order._review_email(self.report_pricing == "priced")

    def print_report(self):
        self.ensure_one()

        report = self.purchase_order.purchase_order_report()
        data = {
            "ids": [self.purchase_order.id],
            "viaduct-parameters": {
                "priced": self.report_pricing == "priced",
            },
        }

        return {
            "type": "ir.actions.report",
            "report_name": report.report_name,
            "report_type": report.report_type,
            "data": data,
        }
