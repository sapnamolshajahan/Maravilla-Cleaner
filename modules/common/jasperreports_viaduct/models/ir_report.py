# -*- coding: utf-8 -*-
from odoo import api, fields, models
from ..viaduct import ViaductReport


class ViaductActionsReport(models.Model):
    _inherit = "ir.actions.report"

    ################################################################################
    # Fields
    ################################################################################
    viaduct_helper = fields.Char("Viaduct Helper classname")

    ################################################################################
    # Business Methods
    ################################################################################
    def is_viaduct_report(self):
        return self.report_file.endswith(".jrxml")

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """
        Override to allow Viaduct rendering
        """
        report_sudo = self._get_report(report_ref)

        if report_sudo.is_viaduct_report():
            data = report_sudo.update_viaduct_data(res_ids, data)
            pdf_content, file_type = ViaductReport(report_sudo).create(res_ids, data)
        else:
            pdf_content, file_type = super(ViaductActionsReport, self)._render_qweb_pdf(report_ref, res_ids, data)

        if file_type == "pdf":
            pdf_content = self.post_process_pdf(pdf_content)

        return pdf_content, file_type

    @api.model
    def post_process_pdf(self, pdf_content):
        """
        Inherit this function to apply any post-processing for PDFs generated
        e.g. used for merging PDF with T&C extensions (see mail_append_pdf module)
        """
        return pdf_content

    def update_viaduct_data(self, res_ids, data):
        """
        Allow sub-classes the opportunity to override; performing pre-report actions and
        possibly transforming report data.

        :param data: report-parameters
        :return: possibly updated report-parameters.
        """
        # Can pass output type with context, if passed then use this one
        output_context = "output-type"
        if self.env.context.get(output_context):
            if not data:
                data = {}
            data[output_context] = self.env.context.get(output_context)
        return data

    def report_action(self, docids, data=None, config=True):

        data = self.update_viaduct_data(docids, data)
        if self.is_viaduct_report():
            # Disable logo-checks, as they're superfluous with JasperReports.
            return super(ViaductActionsReport,
                         self.with_context(discard_logo_check=True)).report_action(docids, data, config)
        return super(ViaductActionsReport, self).report_action(docids, data, config)
