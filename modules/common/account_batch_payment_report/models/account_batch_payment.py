# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountBatchPaymentPrint(models.Model):
    _inherit = "account.batch.payment"

    def print_batch_payment(self):
        report = self.env["ir.actions.report"]._get_report_from_name('account.batch.payment.viaduct')
        return report.report_action(self.ids)
