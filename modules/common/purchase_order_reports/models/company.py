# -*- coding: utf-8 -*-
from odoo import models, fields

PURCHASE_PRINT_BASE_OPTIONS = [
    ("priced", "Priced"),
    ("unpriced", "Unpriced"),
]
PURCHASE_PRINT_OPTIONS = PURCHASE_PRINT_BASE_OPTIONS + [("ask", "Ask User")]


class ResCompany(models.Model):
    _inherit = "res.company"

    ################################################################################
    # Fields
    ################################################################################
    purchase_report_pricing = fields.Selection(PURCHASE_PRINT_OPTIONS, required=True,
                                               default=lambda self: self.env.company.purchase_report_pricing)
    purchase_report_email_review = fields.Boolean(string="Purchase Email Wizard",
                                                  default=lambda self: self.env.company.purchase_report_email_review,
                                                  help="Display email wizard for purchase orders")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ################################################################################
    # Fields
    ################################################################################
    purchase_report_pricing = fields.Selection(related="company_id.purchase_report_pricing",
                                               required=True, readonly=False)
    purchase_report_email_review = fields.Boolean(related="company_id.purchase_report_email_review", readonly=False)

    ################################################################################
    # Methods
    ################################################################################
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.write(
            {
                "purchase_report_pricing": self.purchase_report_pricing,
                "purchase_report_email_review": self.purchase_report_email_review,
            }
        )
