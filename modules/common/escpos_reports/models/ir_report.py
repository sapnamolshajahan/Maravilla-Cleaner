# -*- coding: utf-8 -*-
from odoo import api, models
from ..escpos_report import EscPosReport

ESCPOS_MARKER = "escpos"


class ReportActions(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _render_qweb_text(self, report_ref, docids, data=None):
        """
        Override for ESC/POS rendering, via the report-name.
        """
        if self.is_escpos_report():
            return EscPosReport(self).generate(docids, data)
        return super(ReportActions, self)._render_qweb_text(report_ref, docids, data)

    def is_escpos_report(self):
        return self.report_file == ESCPOS_MARKER
