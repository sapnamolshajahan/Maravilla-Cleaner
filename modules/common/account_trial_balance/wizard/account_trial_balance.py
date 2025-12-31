# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from io import BytesIO as StringIO

import xlsxwriter

from odoo import models, fields


class AccountTrialBalance(models.TransientModel):
    _name = 'account.trial.balance.export'
    _description = 'Account Trial Balance Export'

    report_name = fields.Char(size=64, string='Report Name', readonly=True, default='Trial Balance Report')
    data = fields.Binary(string='Download File', readonly=True)
    as_at_date = fields.Date(string='As at date', required=True)
    report_output = fields.Selection(string='Output file type', selection=[('xls', 'XLSX'), ('pdf', 'PDF')],
                                     required=True, default='xls')

    def _get_account_year(self):
        u"""
        Calculate start and end date of the current accounting year
        :return: start and end date strings
        """
        today = self.as_at_date
        fiscal_last_month = int(self.env.company.fiscalyear_last_month)
        fiscal_last_day = int(self.env.company.fiscalyear_last_day)

        # Need to calculate accounting year here
        if today.month <= fiscal_last_month:
            start_year, end_year = today.year - 1, today.year
        else:
            start_year, end_year = today.year, today.year + 1

        if fiscal_last_month == 12:
            start_date_str = '{year}-{month}-01'.format(year=start_year + 1, month=1)
        else:
            start_date_str = '{year}-{month}-01'.format(year=start_year, month=fiscal_last_month + 1)
        end_date_str = '{year}-{month}-{day}'.format(year=end_year, month=fiscal_last_month, day=fiscal_last_day)
        this_month_start = '{year}-{month}-{day}'.format(year=today.year, month=today.month, day=1)

        return start_date_str, end_date_str, this_month_start

    def get_income_and_exp(self, start_date_str, end_date_str, this_month_start, string_length, company_list):
        self.env.cr.execute(
            """
            select aa.code_store, aa.name, sum(aml.debit) as sum_debit, sum(aml.credit) as sum_credit, 
            sum(aml.debit - aml.credit) as sum_balance,
            sum(CASE
            when aml.date >= %(this_month_start)s and aml.date <= %(end_date)s 
                then aml.debit
            END)  as  month_debit,
             sum(CASE
            when aml.date >= %(this_month_start)s and aml.date <= %(end_date)s then aml.credit 
            END) as  month_credit,
            sum(CASE
            when aml.date >= %(this_month_start)s and aml.date <= %(end_date)s 
                then aml.debit-aml.credit 
            END)  as month_balance
            from account_move_line aml
            join account_account aa on aml.account_id = aa.id
            join account_move am on aml.move_id = am.id
            where (aa.account_type like 'income_%%' or aa.account_type like 'expense_%%' or aa.account_type is null) 
            and am.state = 'posted'
            and aml.date >= %(start_date)s
            and aml.date <= %(end_date)s
            and aml.company_id in (%(company_list)s)
            group by aa.code_store, aa.name
            order by aa.code_store 
            """,
            {
                "this_month_start": this_month_start,
                "start_date": start_date_str,
                "end_date": self.as_at_date,
                "company_list": company_list
            })
        res = self.env.cr.fetchall()
        i_rows = []
        for line in res:
            line = list(line)
            if string_length and self.report_output == 'pdf':
                desc = line[1]
                if not isinstance(line[1], dict):
                    line[1] = desc[:string_length]
                else:
                    line[1] = desc.get('en_US')

            i_rows.append(line)
        return i_rows

    def get_retained_earnings(self, start_date_str, end_date_str, this_month_start, string_length, company_list):

        self.env.cr.execute(
            """
            select 'none' as code, 'Current and Undistributed Earnings' as description, sum(aml.debit) as sum_debit, sum(aml.credit) as sum_credit, 
            sum(aml.debit - aml.credit) as sum_balance,
            0 as month_debit, 
            0 as month_credit,
            0 as month_balance
            from account_move_line aml
            join account_account aa on aml.account_id = aa.id
            join account_move am on aml.move_id = am.id
            where ( aa.account_type like 'income_%%' or aa.account_type like 'expense_%%' or aa.account_type is null) 
            and am.state = 'posted'
            and aml.company_id in (%(company_list)s)
            and aml.date < %(start_date)s
            """,
            {
                "start_date": start_date_str,
                "company_list": company_list
            })

        res = self.env.cr.fetchall()

        i_rows = []
        for line in res:
            line = list(line)
            if string_length and self.report_output == 'pdf':
                desc = line[1]
                if not isinstance(line[1], dict):
                    line[1] = desc[:string_length]
                else:
                    line[1] = desc.get('en_US')
            i_rows.append(line)
        return i_rows

    def get_balance_sheet(self, start_date_str, end_date_str, this_month_start, string_length, company_list):

        self.env.cr.execute(
            """
            select aa.code_store, aa.name, sum(aml.debit) as sum_debit, sum(aml.credit) as sum_credit, sum(aml.debit - aml.credit) as sum_balance,
            sum(CASE
            when aml.date >= %(this_month_start)s and aml.date <= %(end_date)s 
                then aml.debit 
            END)  as  month_debit,
            sum(CASE
            when aml.date >= %(this_month_start)s and aml.date <= %(end_date)s then aml.credit 
            END)  as  month_credit,
            sum(CASE
            when aml.date >= %(this_month_start)s and aml.date <= %(end_date)s 
                then aml.debit-aml.credit 
            END)  as month_balance
            from account_move_line aml
            join account_account aa on aml.account_id = aa.id
            join account_move am on aml.move_id = am.id
            where (aa.account_type not like 'income_%%' and aa.account_type not like 'expense_%%')
            and am.state = 'posted'
            and aml.date <= %(end_date)s
            and aml.company_id in (%(company_list)s)
            group by aa.code_store, aa.name
            order by aa.code_store 
            """,
            {
                "this_month_start": this_month_start,
                "end_date": self.as_at_date,
                "company_list": company_list
            })
        res = self.env.cr.fetchall()
        b_rows = []
        for line in res:
            line = list(line)
            if string_length and self.report_output == 'pdf':
                desc = line[1]
                if not isinstance(line[1], dict):
                    line[1] = desc[:string_length]
                else:
                    line[1] = desc.get('en_US')
                code = line[0]
                if not isinstance(line[0], dict):
                    line[0] = code[:string_length]
                else:
                    line[0] = int(list(code.values())[0])

            b_rows.append(line)

        return b_rows

    def _get_rows_account(self, string_length=False):
        """
        Three queries
        1. get income and expenditure accounts - transactions summed for this year
        2. get retained earnings not distributed to balance sheet
        2. get balance sheet accounts - transactions summed for ever
  
        """

        start_date_str, end_date_str, this_month_start = self._get_account_year()
        company_list = []

        company = self.env.company
        if company.child_ids:
            company_list = [x.id for x in company.childs_ids]
            company_list.append(company.id)
        else:
            company_list = company.id

        rows = []
        rows.extend(
            self.get_income_and_exp(start_date_str, end_date_str, this_month_start, string_length, company_list))
        rows.extend(
            self.get_retained_earnings(start_date_str, end_date_str, this_month_start, string_length, company_list))
        rows.extend(self.get_balance_sheet(start_date_str, end_date_str, this_month_start, string_length, company_list))
        return rows

    def button_process(self):
        """ Create the report"""
        row_date = []
        row_data = self._get_rows_account(60)
        wizard_item = self[0]
        report_date = datetime.strftime(self.as_at_date, '%d-%m-%Y')
        report_name = 'General Ledger Trial Balance Report as at ' + report_date
        heading = ['Code                       ',
                   'Name                                                                                                              ',
                   '             YTD Debit', '             YTD Credit', '             YTD Balance',
                   '             Mth Debit', '             Mth Credit',
                   '             Mth Balance']
        heading_alignment = ['L', 'L', 'R', 'R', 'R', 'R', 'R', 'R']
        if self.report_output == 'pdf':
            self.write({'report_name': self.report_name + '.pdf'})
            output = self.env['pdf.create'].create_pdf(report_name, heading, row_data, True, heading_alignment)
            self.write({'data': output})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.trial.balance.export',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': wizard_item.id,
                'target': 'new',
            }
        # now do standard XLSX output
        self.write({'report_name': self.report_name + '.xlsx'})
        data = StringIO()

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')

        current_date = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), '%d-%m-%Y %H:%M:%S')
        format_number = workbook.add_format({'num_format': '0.00', 'align': 'right'})
        cell_left = workbook.add_format({'align': 'left'})
        cell_centre = workbook.add_format({'align': 'center'})
        cell_right_numeric = workbook.add_format({'align': 'right', 'num_format': '0.00', })
        cell_bold = workbook.add_format({'bold': True})
        row = 1

        worksheet.write(row, 1, self.env.company.name, cell_bold)
        row += 1
        worksheet.write(row, 1, 'Run Date: ' + current_date, cell_bold)
        row += 1
        worksheet.write(row, 1, report_name, cell_bold)
        row += 1
        worksheet.write(row, 1, 'As At: ' + report_date, cell_bold)
        row += 1

        # write headings
        worksheet.write(row, 2, '<----------------------', cell_left)
        worksheet.write(row, 3, 'YTD', cell_centre)
        worksheet.write(row, 4, '---------------------->', cell_right_numeric)
        worksheet.write(row, 5, '<---------------------', cell_left)
        worksheet.write(row, 6, 'Month', cell_centre)
        worksheet.write(row, 7, '--------------------->', cell_right_numeric)
        row += 1
        worksheet.write(row, 0, 'Code', cell_left)
        worksheet.write(row, 1, 'Name', cell_left)
        worksheet.write(row, 2, 'Debit', cell_right_numeric)
        worksheet.write(row, 3, 'Credit', cell_right_numeric)
        worksheet.write(row, 4, 'Balance', cell_right_numeric)
        worksheet.write(row, 5, 'Debit', cell_right_numeric)
        worksheet.write(row, 6, 'Credit', cell_right_numeric)
        worksheet.write(row, 7, 'Balance', cell_right_numeric)

        row += 2
        for item in row_data:
            if isinstance(item[0], dict) and list(item[0].values())[0].isdigit():
                code = int(list(item[0].values())[0])
                worksheet.write(row, 0, code), cell_right_numeric
            else:
                code = item[0]
                worksheet.write(row, 0, code)
            if isinstance(item[1], dict):
                worksheet.write(row, 1, item[1].get('en_US'))
            else:
                worksheet.write(row, 1, item[1])
            worksheet.write(row, 2, item[2], cell_right_numeric)
            worksheet.write(row, 3, item[3], cell_right_numeric)
            worksheet.write(row, 4, item[4], cell_right_numeric)
            worksheet.write(row, 5, item[5], cell_right_numeric)
            worksheet.write(row, 6, item[6], cell_right_numeric)
            worksheet.write(row, 7, item[7], cell_right_numeric)
            row += 1

        row += 2
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:H', 15)
        workbook.close()
        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write({'data': output})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.trial.balance.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard_item.id,
            'target': 'new',
        }
