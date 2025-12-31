# -*- coding: utf-8 -*-
from odoo import api, models

LABEL_TEMPLATE_MARKER = "label.printer.template"


class ReportActions(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _render_qweb_text(self, report_ref, docids, data=None):
        """
        Override for Label Template rendering, via the report-name.
        """
        if not self.is_label_report():
            return super(ReportActions, self)._render_qweb_text(report_ref, docids, data)

        template = self.env["label.printer.template"].current(self.report_name)
        output = []
        for i in docids:
            record = self.env[self.model].browse(i)
            output.append(template.render(record, {}))
        return (b"".join(output), "text")

    def is_label_report(self):
        return self.report_file == LABEL_TEMPLATE_MARKER and self.report_name
