# -*- coding: utf-8 -*-
import io
from odoo import api, models
from collections import defaultdict, OrderedDict


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _prepare_invoice_pdf_report(self, invoices_data):
        """
        Override base-version to allow custom report overrides.

        :param invoice:         An account.move record.
        :param invoice_data:    The collected data for the invoice so far.
        """

        company_id = next(iter(invoices_data)).company_id
        grouped_invoices_by_report = defaultdict(dict)
        for invoice, invoice_data in invoices_data.items():
            invoice_data['pdf_report'] = invoice.get_invoice_report()
            grouped_invoices_by_report[invoice_data['pdf_report']][invoice] = invoice_data

        for pdf_report, group_invoices_data in grouped_invoices_by_report.items():
            ids = [inv.id for inv in group_invoices_data]

            content, report_type = self.env['ir.actions.report'].with_company(company_id)._render_qweb_pdf(
                pdf_report.report_name, res_ids=ids)

            for invoice, invoice_data in group_invoices_data.items():
                invoice_data['pdf_attachment_values'] = {
                    'name': invoice._get_invoice_report_filename(),
                    'raw': content,
                    'mimetype': 'application/pdf',
                    'res_model': invoice._name,
                    'res_id': invoice.id,
                    'res_field': 'invoice_pdf_report_file',
                }

    @api.model
    def _prepare_invoice_proforma_pdf_report(self, invoice, invoice_data):
        """
        Override base-version to allow custom report overrides.

        :param invoice:         An account.move record.
        :param invoice_data:    The collected data for the invoice so far.
        """
        content, _report_format = self.env["ir.actions.report"]._render(
            invoice.get_invoice_report().report_name, invoice.ids, data={"proforma": True})

        invoice_data["proforma_pdf_attachment_values"] = {
            "raw": content,
            "name": invoice._get_invoice_proforma_pdf_report_filename(),
            "mimetype": "application/pdf",
            "res_model": invoice._name,
            "res_id": invoice.id,
        }
