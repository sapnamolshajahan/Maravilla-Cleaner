# -*- coding: utf-8 -*-
from datetime import datetime
from io import BytesIO as StringIO

import xlsxwriter

from odoo import models, fields


class AgedTrialBalanceByCurrencyReport(models.TransientModel):
    """ Aged Trial Balance by Currency to XLS
    """
    _name = "aged.trial.balance.currency.xls.report"
    _description = 'Ar and AP Currency Report'

    name = fields.Char(string="Unused")

    def run_report(self, wizard):
        """ Create the report.
        """
        report_name = 'Aged Trial Balance By Currency'
        file_name = "{0}.xlsx".format(report_name)

        data = StringIO()
        workbook = xlsxwriter.Workbook(data)
        worksheet = workbook.add_worksheet('Data')

        # write report header
        row = 0
        worksheet.write(row, 0, 'Aged Trial Balance as at: ' + str(wizard.as_at_date))
        row += 1
        worksheet.write(row, 0, 'Run Date-Time: ' + fields.Datetime.to_string(fields.Datetime.context_timestamp(self, datetime.now())))
        row += 2

        # write headings
        columns_map = {
            0: 'Code',
            1: 'Name',
            2: 'Balance',
            3: 'Current',
            4: '30 days',
            5: '60 days',
            6: '90 days',
            7: '120+ days'
        }

        for key, value in columns_map.items():
            worksheet.write(row, key, value)
        row += 2

        # Now select the records
        lines = self.env["res.partner.statement.lines"].search(
            [('res_partner_statement_id', '=', wizard.id)], order="currency_id,sort_name"
        )
        self.by_currency_report(lines, worksheet, workbook, row, wizard)
        workbook.close()

        return report_name, file_name, "Aged Trial Balance by Currency", data

    def by_currency_report(self, lines, worksheet, workbook, row, wizard):

        format_total_cell = workbook.add_format({'bold': True, 'num_format': '0.00', 'align': 'right'})
        sorted_lines = lines

        name = sorted_lines and sorted_lines[0].sort_name or ''
        ref = sorted_lines and sorted_lines[0].transaction_partner_id.ref or False
        current_currency_name = sorted_lines and sorted_lines[0].currency_id.name or False
        balance = period0 = period1 = period2 = period3 = period4 = 0
        curr_tot_balance = curr_tot_period0 = curr_tot_period1 = curr_tot_period2 = curr_tot_period3 = curr_tot_period4 = 0

        for line in sorted_lines:
            if line.sort_name != name and line.currency_id.name != current_currency_name:
                worksheet.write(row, 0, ref)
                worksheet.write(row, 1, name)
                worksheet.write(row, 2, balance)
                worksheet.write(row, 3, period0)
                worksheet.write(row, 4, period1)
                worksheet.write(row, 5, period2)
                worksheet.write(row, 6, period3)
                worksheet.write(row, 7, period4)
                row += 1

                worksheet.write(row, 0, 'Total for ')
                worksheet.write(row, 1, current_currency_name)
                worksheet.write(row, 2, curr_tot_balance, format_total_cell)
                worksheet.write(row, 3, curr_tot_period0, format_total_cell)
                worksheet.write(row, 4, curr_tot_period1, format_total_cell)
                worksheet.write(row, 5, curr_tot_period2, format_total_cell)
                worksheet.write(row, 6, curr_tot_period3, format_total_cell)
                worksheet.write(row, 7, curr_tot_period4, format_total_cell)
                row += 2
                curr_tot_balance = curr_tot_period0 = curr_tot_period1 = curr_tot_period2 = curr_tot_period3 = curr_tot_period4 = 0
                current_currency_name = line.currency_id.name or False

                period4 = line.period4
                period3 = line.period3
                period2 = line.period2
                period1 = line.period1
                period0 = line.period0
                balance = line.balance

                curr_tot_period4 += line.period4
                curr_tot_period3 += line.period3
                curr_tot_period2 += line.period2
                curr_tot_period1 += line.period1
                curr_tot_period0 += line.period0
                curr_tot_balance += line.balance

                name = line.sort_name
                ref = line.transaction_partner_id.ref or False

            elif line.sort_name != name:
                worksheet.write(row, 0, ref)
                worksheet.write(row, 1, name)
                worksheet.write(row, 2, balance)
                worksheet.write(row, 3, period0)
                worksheet.write(row, 4, period1)
                worksheet.write(row, 5, period2)
                worksheet.write(row, 6, period3)
                worksheet.write(row, 7, period4)
                row += 1

                period4 = line.period4
                period3 = line.period3
                period2 = line.period2
                period1 = line.period1
                period0 = line.period0
                balance = line.balance

                curr_tot_period4 += line.period4
                curr_tot_period3 += line.period3
                curr_tot_period2 += line.period2
                curr_tot_period1 += line.period1
                curr_tot_period0 += line.period0
                curr_tot_balance += line.balance

                name = line.sort_name
                ref = line.transaction_partner_id.ref or False

            else:
                period4 += line.period4
                period3 += line.period3
                period2 += line.period2
                period1 += line.period1
                period0 += line.period0
                balance += line.balance

                curr_tot_period4 += line.period4
                curr_tot_period3 += line.period3
                curr_tot_period2 += line.period2
                curr_tot_period1 += line.period1
                curr_tot_period0 += line.period0
                curr_tot_balance += line.balance

        # cater for last partner and currency
        if len(sorted_lines):
            worksheet.write(row, 0, line.transaction_partner_id.ref or False)
            worksheet.write(row, 1, line.sort_name)
            worksheet.write(row, 7, period4)
            worksheet.write(row, 6, period3)
            worksheet.write(row, 5, period2)
            worksheet.write(row, 4, period1)
            worksheet.write(row, 3, period0)
            worksheet.write(row, 2, balance)
            row += 1

            worksheet.write(row, 0, 'Total for ')
            worksheet.write(row, 1, current_currency_name)
            worksheet.write(row, 7, curr_tot_period4, format_total_cell)
            worksheet.write(row, 6, curr_tot_period3, format_total_cell)
            worksheet.write(row, 5, curr_tot_period2, format_total_cell)
            worksheet.write(row, 4, curr_tot_period1, format_total_cell)
            worksheet.write(row, 3, curr_tot_period0, format_total_cell)
            worksheet.write(row, 2, curr_tot_balance, format_total_cell)
            row += 1
