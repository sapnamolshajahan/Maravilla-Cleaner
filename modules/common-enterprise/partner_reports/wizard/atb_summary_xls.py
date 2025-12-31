# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO as StringIO

import xlsxwriter
from odoo.exceptions import UserError

from odoo import models, fields


class AgedTrialBalanceReport(models.TransientModel):
    """ Aged Trial Balance to XLS"""
    _name = 'aged.trial.balance.xls.report'
    _description = 'Ar and AP Summary Report'

    ###########################################################################
    # Fields
    ###########################################################################

    name = fields.Char(string="Unused")

    def remove_not_in_credit(self, lines):
        partner_set = set([x.transaction_partner_id for x in lines])
        for partner in partner_set:
            partner_lines = [x for x in lines if x.transaction_partner_id.id == partner.id]
            balance = sum([x.balance for x in partner_lines])
            if balance > 0:
                for line in partner_lines:
                    line.write({'ignore': True})

    def remove_not_overdue(self, lines):
        partner_set = set([x.transaction_partner_id for x in lines])
        for partner in partner_set:
            partner_lines = [x for x in lines if x.transaction_partner_id.id == partner.id]
            overdue = sum([x.period1 + x.period2 + x.period3 + x.period4 for x in partner_lines])
            if not overdue:
                for line in partner_lines:
                    line.write({'ignore': True})

    def run_report(self, wizard):
        if wizard.as_at_date:
            report_date = wizard.as_at_date
        else:
            report_date = wizard.date_from
        report_date = report_date

        report_title = self.get_report_title(wizard)
        report_name = self.get_report_name(wizard, report_date)
        file_name = self.get_filename(wizard, report_date)

        currency_id = wizard.statement_currency.id
        company_currency = self.env.company.currency_id.id
        if currency_id and currency_id != company_currency:
            currency = wizard.statement_currency.id
        else:
            currency = False

        lines = self.env["res.partner.statement.lines"].search([('res_partner_statement_id', '=', wizard.id)])
        if wizard.in_credit:
            self.remove_not_in_credit(lines)

        if wizard.overdue_only:
            self.remove_not_overdue(lines)

        if not lines:
            raise UserError('No lines to process')

        return self.generate_xlsx(lines, wizard, currency, report_date, report_name, report_title, file_name)

    def generate_pdf(self, lines, wizard, currency, report_date, report_name, report_title, file_name):
        """
        this is spaced out as we set the column widths based on the actual spacing below
        """
        heading = [
            "{:26}".format("Ref"),
            "{:130}".format("Name"),
            "{:>21}".format("Balance"),
            "{:>21}".format("Current"),
            "{:>21}".format("30 days"),
            "{:>21}".format("60 days"),
            "{:>21}".format("90 days"),
            "{:>21}".format("120+ days"),
        ]
        heading_alignment = ['L', 'L', 'R', 'R', 'R', 'R', 'R', 'R']
        row_data = self.build_data_lines(lines, wizard, currency)
        output = self.env['pdf.create'].create_raw_pdf(report_name, heading, row_data, True, heading_alignment)
        return report_name, file_name, report_title, StringIO(output)

    def generate_xlsx(self, lines, wizard, currency, report_date, report_name, report_title, file_name):

        data = StringIO()

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')
        row = 0
        worksheet.write(row, 0, report_title + str(report_date))
        row += 1
        worksheet.write(row, 0, 'Run Date-Time: ' + fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, datetime.now())))
        cell_right_numeric = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        row += 1

        if wizard.statement_currency:
            worksheet.write(row, 0, 'Currency: ' + wizard.statement_currency.name)
        else:
            worksheet.write(row, 0, 'Currency: None')

        row = self.output_xls_header(worksheet, row + 2, self.build_header_list(wizard))

        data_lines = self.build_data_lines(lines, wizard, currency)
        self.output_xls_lines(data_lines, worksheet, row, cell_right_numeric)
        workbook.close()
        return report_name, file_name, "ATB Summary Report", data

    def get_report_title(self, wizard):

        if wizard.type == "asset_receivable":
            return "Accounts Receivable ATB Report"
        return "Accounts Payable ATB Report"

    def get_report_name(self, wizard, report_date):

        return "{0} as at {1}".format(self.get_report_title(wizard), report_date)

    def get_filename(self, wizard, report_date):
        return "{0}.xlsx".format(self.get_report_name(wizard, report_date))

    def build_header_list(self, wizard):
        if wizard.aging == "months":
            return [
                "Code",
                "Name",
                "Balance",
                "Current",
                "30 days",
                "60 days",
                "90 days",
                "120+ days",
            ]

        header_list = ["Code", "Name", "Balance"]
        from_num = 1
        to_num = wizard.days
        for i in range(0, 5):
            header_list.append("{} - {}".format(from_num, to_num))
            from_num = to_num + 1
            to_num += wizard.days
        return header_list

    def output_xls_header(self, worksheet, row_begin, headers):

        col = 0
        for header in headers:
            worksheet.write(row_begin, col, header)
            col += 1
        return row_begin + 2

    def output_xls_lines(self, data_lines, worksheet, row, cell_right_numeric):

        for data_line in data_lines:
            self.output_xls_line(data_line, worksheet, row, cell_right_numeric)
            row += 1
        return row

    def output_xls_line(self, line_data, worksheet, row, numeric_format):
        worksheet.write(row, 0, line_data[0])
        worksheet.write(row, 1, line_data[1])
        worksheet.write(row, 2, line_data[2], numeric_format)
        worksheet.write(row, 3, line_data[3], numeric_format)
        worksheet.write(row, 4, line_data[4], numeric_format)
        worksheet.write(row, 5, line_data[5], numeric_format)
        worksheet.write(row, 6, line_data[6], numeric_format)
        worksheet.write(row, 7, line_data[7], numeric_format)

    def accum_values_for_partner(self, line, line_list):
        line_list[0] = line.transaction_partner_id.ref
        line_list[1] = line.transaction_partner_id.name
        line_list[2] += line.balance
        line_list[3] += line.period0
        line_list[4] += line.period1
        line_list[5] += line.period2
        line_list[6] += line.period3
        line_list[7] += line.period4
        return line_list

    def build_data_line(self, line, wizard):
        """
        :param line: res.partner.statement.lines
        :param groupdebtor:
        :return: line data in a list
        """
        line_result = ["", "", 0, 0, 0, 0, 0, 0]
        if wizard.groupdebtor:
            line_result[0] = ''
            line_result[1] = line.groupdebtor_name
        else:
            line_result[0] = line.transaction_partner_id.ref
            line_result[1] = line.transaction_partner_id.name
        line_result[2] = line.balance
        line_result[3] = line.period0
        line_result[4] = line.period1
        line_result[5] = line.period2
        line_result[6] = line.period3
        line_result[7] = line.period4
        return line_result

    def line_key(self, line, wizard):
        if wizard.groupdebtor:
            return line.groupdebtor_name
        return "{}.{}".format(line.sort_name, line.transaction_partner_id.id)

    def build_data_lines(self, lines, wizard, currency):

        if wizard.groupdebtor:
            sorted_lines = sorted(lines, key=lambda line_id: line_id.groupdebtor_name)
        else:
            lines = lines.filtered(lambda l: l.transaction_partner_id and l.sort_name)

            sorted_lines = sorted(lines, key=lambda line_id: (
                line_id.sort_name, line_id.transaction_partner_id.id, line_id.id))

        last_line_key = ""
        total_period0 = total_period1 = total_period2 = total_period3 = total_period4 = total_balance = 0

        data_lines = []
        line_list = []
        for line in sorted_lines:
            if line.ignore:
                continue

            if currency and line.currency_id != currency:
                continue

            total_balance += line.balance
            total_period0 += line.period0
            total_period1 += line.period1
            total_period2 += line.period2
            total_period3 += line.period3
            total_period4 += line.period4

            this_line_key = self.line_key(line, wizard)
            if this_line_key != last_line_key:
                if line_list:
                    data_lines.append(line_list)
                line_list = self.build_data_line(line, wizard)
                last_line_key = this_line_key
            else:
                line_list = self.accum_values_for_partner(line, line_list)

        # write line for last partner
        if line_list:
            data_lines.append(line_list)

        # write total line
        data_lines.append(['Grand Total', '', total_balance, total_period0, total_period1, total_period2,
                           total_period3, total_period4])

        return data_lines
