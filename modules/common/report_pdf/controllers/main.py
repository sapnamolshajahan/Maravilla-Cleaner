# -*- coding: utf-8 -*-

from fpdf import FPDF
from odoo import http
from datetime import datetime
from odoo.addons.web.controllers.export import Export, ExportFormat


class PdfExport(Export):

    @http.route("/web/export/formats", type="json", auth="user")
    def formats(self):
        """ Returns all valid export formats
        :returns: for each export format, a pair of identifier and printable name
        :rtype: [(str, str)]
        """
        result = super(PdfExport, self).formats()
        result.append({"tag": "pdf", "label": "PDF"})
        return result

class PDFExport(ExportFormat, http.Controller):

    @http.route("/web/export/pdf", type="http", auth="user")
    def index(self, data):
        return self.base(data)

    @property
    def extension(self):
        return '.pdf'

    @property
    def content_type(self):
        return "application/pdf"

    def filename(self, base):
        return base + ".pdf"

    def add_standard_heading(self, pdf, report_name):
        current_date = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        run_date = "Run Date/Time:" + " " + current_date
        pdf.set_font("arial", "B", 10.0)
        pdf.cell(ln=1, h=5.0, align="L", w=0, txt=http.request.env.company.partner_id.name, border=0)
        pdf.cell(ln=1, h=5.0, align="L", w=0, txt=run_date, border=0)
        pdf.cell(ln=1, h=5.0, align="L", w=0, txt=report_name, border=0)
        pdf.ln()
        return pdf

    def add_column_headings(self, pdf, headings, sample_row):
        pdf.set_font("arial", "B", 10.0)
        number_of_columns = len(headings)
        col_vals = {}
        max_string_length = {}

        # Calculate column widths based on headings and sample_row
        for i in range(number_of_columns):
            max_length = len(headings[i])  # Base column width on heading length

            # If a sample row exists, consider its data for width calculation
            if sample_row:
                if isinstance(sample_row, (list, tuple)):
                    sample_value = str(sample_row[i])
                elif isinstance(sample_row, dict):
                    sample_value = str(sample_row.get(i, ""))
                else:
                    sample_value = ""

                max_length = max(max_length, len(sample_value))

            # Set alignment and width
            alignment = "R" if isinstance(sample_row[i], (int, float)) else "L"
            width = max(min(max_length * 5, 50), 15)  # Width between 15 and 50
            col_vals[i] = (alignment, width)
            max_string_length[i] = width // 5  # Approx. max chars based on width

        # Add the column headings to the PDF
        for i in range(number_of_columns):
            pdf.cell(
                ln=0, h=6.0, align=col_vals[i][0], w=col_vals[i][1], txt=headings[i], border=1
            )
        pdf.ln()

        return pdf, number_of_columns, col_vals, max_string_length

    def from_data(self, fields, columns_headers, rows):
        pdf = FPDF()
        pdf.compress = False
        pdf.add_page(orientation="L")
        pdf.set_xy(0, 0)

        # Use column_headers if provided, otherwise default to fields
        headers = columns_headers if columns_headers else fields

        if not rows:
            value_set = []
        elif isinstance(rows, dict):
            key = next(iter(rows))
            value_set = rows[key] if rows[key] else []
        else:
            value_set = rows[0] if rows else []

        # Add standard heading
        pdf = self.add_standard_heading(pdf, "Report Title")

        # Add column headings
        pdf, number_of_columns, col_vals, max_string_length = self.add_column_headings(pdf, headers, value_set)

        pdf.set_font("arial", "", 10.0)

        # Process rows (dictionary or list)
        if isinstance(rows, dict):
            for row in rows.values():
                for i in range(0, number_of_columns):
                    txt = (
                        "{:10.2f}".format(row[i]) if isinstance(row[i], float) else str(row[i])
                    )
                    # Truncate text if needed
                    if len(txt) > max_string_length.get(i, 15):
                        txt = txt[:max_string_length[i]]
                    pdf.cell(ln=0, h=5.0, align=col_vals[i][0], w=col_vals[i][1], txt=txt, border=0)
                pdf.ln()
        else:
            for row in rows:
                for i in range(0, number_of_columns):
                    txt = (
                        "{:10.2f}".format(row[i]) if isinstance(row[i], float) else str(row[i])
                    )
                    # Truncate text if needed
                    if len(txt) > max_string_length.get(i, 15):
                        txt = txt[:max_string_length[i]]
                    pdf.cell(ln=0, h=5.0, align=col_vals[i][0], w=col_vals[i][1], txt=txt, border=0)
                pdf.ln()

        # Return PDF as binary string
        return pdf.output(dest="S").encode("latin1")
