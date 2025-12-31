# -*- coding: utf-8 -*-

import base64
from fpdf import FPDF
from datetime import datetime
from odoo import models, fields


class PDFCreate(models.Model):
    _name = 'pdf.create'
    _description = 'PDF Create'

    def add_standard_heading(self, pdf, report_name):

        current_date = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), '%Y-%m-%d %H:%M:%S')
        run_date = 'Run Date/Time:' + ' ' + current_date
        pdf.set_font('arial', 'B', 10.0)
        pdf.cell(ln=1, h=5.0, align='L', w=0, txt=self.env.company.partner_id.name, border=0)
        pdf.cell(ln=1, h=5.0, align='L', w=0, txt=run_date, border=0)
        pdf.cell(ln=1, h=5.0, align='L', w=0, txt=report_name, border=0)
        pdf.ln()
        return pdf

    def add_column_headings(self, pdf, heading, value_set, use_heading, heading_alignment):

        if heading_alignment:
            number_of_columns = len(heading_alignment)

        elif value_set:
            number_of_columns = len(value_set)
        else:
            number_of_columns = 0

        default_width = (number_of_columns and int(280 / number_of_columns)) or 0

        max_string_length = {}
        pdf.set_font('arial', 'B', 10.0)
        col_vals = {}
        if use_heading:
            for i in range(0, number_of_columns):
                if heading_alignment[i] == 'R':
                    col_vals[i] = 'R', len(heading[i])
                    max_string_length[i] = len(heading[i])
                    pdf.cell(ln=0, h=5.0, align='R', w=len(heading[i]), txt=heading[i], border=0)
                else:
                    col_vals[i] = 'L', len(heading[i])
                    max_string_length[i] = len(heading[i])
                    pdf.cell(ln=0, h=5.0, align='L', w=len(heading[i]), txt=heading[i], border=0)
            pdf.ln()
            return pdf, number_of_columns, col_vals, max_string_length
        else:
            for i in range(0, number_of_columns):
                if isinstance(value_set[i], float):
                    col_vals[i] = 'R', 20
                    max_string_length[i] = 20
                else:
                    if len(str(value_set[i])) < 15 and len(heading[i]) < 15:
                        col_vals[i] = 'L', default_width
                        max_string_length[i] = default_width
                    elif len(heading[i]) > 15:
                        col_vals[i] = 'L', len(heading[i]) + 2
                        max_string_length[i] = len(heading[i])
                    else:
                        col_vals[i] = 'L', len(str(value_set[i]) * 2)
                        max_string_length[i] = len(str(value_set[i]))

        for i in range(0, number_of_columns):
            try:
                if i < (number_of_columns - 1) and col_vals[i][0] == 'L' and col_vals[i + 1][0] == 'R':
                    width = col_vals[i][1] + col_vals[i + 1][1]
                else:
                    width = col_vals[i][1]
            except:
                width = max_string_length[i]
            pdf.cell(ln=0, h=5.0, align=col_vals[i][0], w=width, txt=heading[i], border=0)
        pdf.ln()

        return pdf, number_of_columns, col_vals, max_string_length

    def create_pdf(self, report_name, heading, row_data, use_heading=False, heading_alignment=False):
        """
            @return base64 encoded pdf
        """
        return base64.encodebytes(self.create_raw_pdf(report_name, heading, row_data, use_heading, heading_alignment))

    def create_raw_pdf(self, report_name, heading, row_data, use_heading=False, heading_alignment=False):
        """
        :param use_heading: if True then columns widths are set by the heading format passed in,
        otherwise are calculated based on data in columns and using defaults
        """
        pdf = FPDF()
        pdf.add_page(orientation='L')
        pdf.compress = False
        pdf.set_xy(0, 0)

        if not row_data:
            value_set = False

        elif isinstance(row_data, dict):
            key = next(iter(row_data))
            if isinstance(row_data[key], dict):  # cater for dict with sub dict - 1 extra level only
                second_key = next(iter(row_data[key]))
                value_set = row_data[key][second_key]
            else:
                value_set = row_data[key]
        else:
            value_set = row_data[0]

        pdf = self.add_standard_heading(pdf, report_name)
        pdf, number_of_columns, col_vals, max_string_length = self.add_column_headings(
            pdf, heading, value_set, use_heading, heading_alignment
        )
        pdf.set_font('arial', '', 10.0)

        if isinstance(row_data, dict):
            for key in sorted(iter(row_data.keys())):
                row = row_data[key]
                if isinstance(row_data[key], dict):
                    for inner_key in sorted(iter(row_data[key].keys())):
                        record = row_data[key][inner_key]
                        for i in range(0, number_of_columns):
                            if isinstance(record[i], float):
                                txt = "{:10.2f}".format(record[i])
                            else:
                                txt = str(record[i])
                            if len(txt) > max_string_length[i]:
                                txt = txt[:max_string_length[i]]
                            if i < (number_of_columns - 1) and col_vals[i][0] == 'L' and col_vals[i + 1][0] == 'R' and not use_heading:
                                width = col_vals[i][1] + col_vals[i + 1][1]
                            else:
                                width = col_vals[i][1]
                            pdf.cell(ln=0, h=5.0, align=col_vals[i][0], w=width, txt=txt, border=0)
                        pdf.ln()
                else:
                    for i in range(0, number_of_columns):
                        if isinstance(row[i], float):
                            txt = "{:10.2f}".format(row[i])
                        else:
                            txt = str(row[i])
                            if len(txt) > max_string_length[i]:
                                txt = txt[:max_string_length[i]]
                        if i < (number_of_columns - 1) and col_vals[i][0] == 'L' and col_vals[i + 1][0] == 'R' and not use_heading:
                            width = col_vals[i][1] + col_vals[i + 1][1]
                        else:
                            width = col_vals[i][1]
                        pdf.cell(ln=0, h=5.0, align=col_vals[i][0], w=width, txt=txt, border=0)
                pdf.ln()

        else:
            for row in row_data:
                for i in range(0, number_of_columns):
                    if isinstance(row[i], float):
                        txt = "{:10.2f}".format(row[i])
                    else:
                        txt = str(row[i])
                        if len(txt) > max_string_length[i]:
                            txt = txt[:max_string_length[i]]
                    if i < (number_of_columns - 1) and col_vals[i][0] == 'L' and col_vals[i + 1][0] == 'R' and not use_heading:
                        width = col_vals[i][1] + col_vals[i + 1][1]
                    else:
                        width = col_vals[i][1]
                    pdf.cell(ln=0, h=5.0, align=col_vals[i][0], w=width, txt=txt, border=0)
                pdf.ln()

        return pdf.output(dest='s').encode()
