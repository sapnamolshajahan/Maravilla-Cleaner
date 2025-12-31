# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime
from io import BytesIO as StringIO

import xlsxwriter
from odoo.exceptions import UserError

from odoo import models, fields


class DetailAgedTrialBalanceReport(models.TransientModel):
    """ Detailed Aged Trial Balance to XLS
    """
    _name = "detailed.aged.trial.balance.report"
    _description = 'Ar and AP Detail Report'

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
        """ Create the report.
        """

        if wizard.as_at_date:
            report_date = wizard.as_at_date
        else:
            report_date = wizard.date_from

        if wizard.type == 'asset_receivable':
            report_title = 'Accounts Receivable ATB Report '
        else:
            report_title = 'Accounts Payable ATB Report '

        report_name = report_title + 'as at ' + str(report_date)

        file_name = "{0}.xlsx".format(report_name)

        currency_id = wizard.statement_currency.id
        company_currency = self.env.company.currency_id.id
        if currency_id and currency_id != company_currency:
            currency = wizard.statement_currency.id
        else:
            currency = False

        lines = self.env["res.partner.statement.lines"].search(
            [('res_partner_statement_id', '=', wizard.id)])

        if wizard.in_credit:
            self.remove_not_in_credit(lines)

        if wizard.overdue_only:
            self.remove_not_overdue(lines)

        if not lines:
            raise UserError('No lines to process')

        data = StringIO()
        workbook = xlsxwriter.Workbook(data)
        worksheet = workbook.add_worksheet('Data')

        row = 0
        cell_right_numeric = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        # write report header
        worksheet.write(row, 0, report_title + str(report_date))
        row += 1
        worksheet.write(row, 0, 'Run Date-Time: ' + fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, datetime.now())))
        row += 1
        worksheet.write(row, 0, 'Currency: ' + str(wizard.statement_currency.name))
        row += 2

        columns_map = {
            0: 'Ref',
            1: 'Name',
            2: 'Trans Ref',
            3: 'Date',
        }
        if wizard.aging == 'months':
            columns_map = {
                4: 'Balance',
                5: 'Current',
                6: '30 days',
                7: '60 days',
                8: '90 days',
                9: '120+ days'
            }
        else:
            from_num = 1
            to_num = wizard.days
            for i in range(4, 10):
                columns_map[i] = str(from_num) + ' - ' + str(to_num)
                from_num = to_num + 1
                to_num += wizard.days

        for key, value in columns_map.items():
            worksheet.write(row, key, value)
        row += 2

        data_dict = self.build_dict(lines, currency, 999)
        self.output_xls_lines(data_dict, worksheet, row, cell_right_numeric)

        workbook.close()
        return report_name, file_name, "Detailed Aged Trial Balance Report", data

    def output_xls_lines(self, data_dict, worksheet, row, cell_right_numeric):

        for key in sorted(data_dict.keys()):
            for inner_key in sorted(data_dict[key].keys()):
                record = data_dict[key][inner_key]
                worksheet.write(row, 0, record[0])
                worksheet.write(row, 1, record[1])
                worksheet.write(row, 2, record[2], cell_right_numeric)
                worksheet.write(row, 3, record[3], cell_right_numeric)
                worksheet.write(row, 4, record[4], cell_right_numeric)
                worksheet.write(row, 5, record[5], cell_right_numeric)
                worksheet.write(row, 6, record[6], cell_right_numeric)
                worksheet.write(row, 7, record[7], cell_right_numeric)
                worksheet.write(row, 8, record[8], cell_right_numeric)
                worksheet.write(row, 9, record[9], cell_right_numeric)
                row += 1

    def create_line_dict(self, line, first_row, name_length):
        line_result = ["", "", "", "", 0, 0, 0, 0, 0, 0]
        if first_row:
            name = line.transaction_partner_id.name
            line_result[0] = line.transaction_partner_id.ref
            line_result[1] = name[:name_length]
            first_row = False
        line_result[2] = line.invoice_number[0:20]
        line_date = line.date
        formatted_line_date = datetime.strftime(line_date, '%d-%m-%Y')
        line_result[3] = formatted_line_date
        line_result[9] = line.period4
        line_result[8] = line.period3
        line_result[7] = line.period2
        line_result[6] = line.period1
        line_result[5] = line.period0
        line_result[4] = line.balance
        return line_result, first_row

    def create_total_line(self, period4, period3, period2, period1, period0, balance):
        # create a total line for the partner as a separate dict
        total_line = ['', '', '', '', '', '', '', '', '', '']
        total_line[2] = 'Total'
        total_line[9] = period4
        total_line[8] = period3
        total_line[7] = period2
        total_line[6] = period1
        total_line[5] = period0
        total_line[4] = balance
        return total_line

    def build_dict(self, lines, currency, name_length):
        dict_of_results = defaultdict(dict)

        lines = lines.filtered(lambda l: l.transaction_partner_id)
        sorted_lines = sorted(lines, key=lambda l: (l.sort_name, l.transaction_partner_id.id, l.date))

        if sorted_lines:
            unique_key = sorted_lines[0].sort_name + '.' + str(sorted_lines[0].transaction_partner_id.id)
            name = sorted_lines[0].sort_name
        else:
            unique_key = ''
            name = ''
        transaction_partner = sorted_lines[0].transaction_partner_id.id

        balance = period0 = period1 = period2 = period3 = period4 = 0
        total_period0 = total_period1 = total_period2 = total_period3 = total_period4 = total_balance = 0
        first_row = True

        for line in sorted_lines:
            if line.ignore:
                continue

            if currency and line.currency_id != currency:
                continue

            if line.sort_name + '.' + str(line.transaction_partner_id.id) == name + '.' + str(
                    transaction_partner):  # line for same partner
                line_result, first_row = self.create_line_dict(line, first_row, name_length)
                dict_of_results[unique_key]['A' + str(line.date) + str(line.id)] = line_result

                period4 += line.period4
                period3 += line.period3
                period2 += line.period2
                period1 += line.period1
                period0 += line.period0
                balance += line.balance

            else:
                # write the total line
                total_line = self.create_total_line(period4, period3, period2, period1, period0, balance)
                dict_of_results[unique_key]['T' + str(line.id)] = total_line
                # write a space line and set new unique key up for the main dict
                dict_of_results[unique_key]['Z' + str(line.id)] = ['', '', '', '', '', '', '', '', '', '']

                # now write this line for the new partner
                line_result, first_row = self.create_line_dict(line, True, name_length)
                unique_key = line.sort_name + '.' + str(line.transaction_partner_id.id)
                dict_of_results[unique_key]['A' + str(line.date) + str(line.id)] = line_result

                name = line.sort_name
                transaction_partner = line.transaction_partner_id.id
                # reset the totals
                period4 = line.period4
                period3 = line.period3
                period2 = line.period2
                period1 = line.period1
                period0 = line.period0
                balance = line.balance

            # accum grand totals for report
            total_period0 += line.period0
            total_period1 += line.period1
            total_period2 += line.period2
            total_period3 += line.period3
            total_period4 += line.period4
            total_balance += line.balance

        # write the total line for the last partner
        total_line = self.create_total_line(period4, period3, period2, period1, period0, balance)
        dict_of_results[unique_key]['T' + str(line.id)] = total_line
        dict_of_results[unique_key]['Z' + str(line.id)] = ['', '', '', '', '', '', '', '', '', '']

        # now create a total line for the report

        unique_key = 'zzzzzz'
        dict_of_results[unique_key]['GT1'] = ['', '', '', '', '', '', '', '', '', '']
        dict_of_results[unique_key]['GT2'] = ['', '', '', '', '', '', '', '', '', '']
        dict_of_results[unique_key]['GT3'] = ['Grand Total', '', '', '', total_balance, total_period0, total_period1,
                                              total_period2, total_period3, total_period4]

        return dict_of_results
