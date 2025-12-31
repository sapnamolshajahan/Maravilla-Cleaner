# -*- coding: utf-8 -*-
from io import BytesIO as cStringIO

from odoo import models, fields


class DetailAgedTrialBalancePdfReport(models.TransientModel):
    """
    Detailed Aged Trial Balance as PDF
    """
    _name = "detailed.aged.trial.balance.pdf.report"
    _description = 'Ar and AP PDF Report'

    ###########################################################################
    #
    # - Fields
    #
    ###########################################################################

    name = fields.Char(string="Unused")

    def get_report(self, wizard):
        """
        Override to use custom report.

        :return: ir.actions.report record
        """
        if self.env.company.currency_id.id == wizard.statement_currency.id:
            return self.env.ref("partner_reports.generic_detailed_atb")
        return self.env.ref("partner_reports.generic_detailed_atb_forex")

    def run_report(self, wizard):
        report = self.get_report(wizard)
        report_data = {
            "viaduct-parameters": {
                "order-by": "groupdebtor_name" if wizard.groupdebtor else "sort_name",
            }
        }

        self.env.cr.commit()  # forced commit to allow Viaduct to view records
        result, rpt_format = report._render(report, wizard.ids, report_data)

        return report.name, "{0}.{1}".format(report.name, rpt_format), "Detailed ATB", cStringIO(result)
