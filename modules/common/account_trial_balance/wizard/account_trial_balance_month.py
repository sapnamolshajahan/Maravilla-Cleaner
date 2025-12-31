# -*- coding: utf-8 -*-
"""
This is the multi-month report
"""

import base64
from datetime import datetime
from io import BytesIO as StringIO

import xlsxwriter

from odoo import models, fields


class AccountTrialBalanceMonth(models.TransientModel):
    _name = 'account.trial.balance.month.export'
    _description = 'Account Trial Balance Month Export'

    report_name = fields.Char(size=64, string='Report Name', readonly=True, default='Trial Balance Monthly Report.xlsx')
    data = fields.Binary(string='Download File', readonly=True)
    as_at_date = fields.Date(string='As at date', required=True)
    from_date = fields.Date(string='From Date', required=True,
                            help='Starting with this month, the report will produce a trial balance for each month.' \
                                 'For Income & Expenditure accounts this is the net transactions for the month' \
                                 'For Balance Sheet accounts it is the closing balance at the end of the month')

    def _get_rows_account(self):
        """
        Three queries
        1. get income and expenditure accounts - transactions summed by period
        2. get balance sheet accounts - transactions summed for ever, balance at end of each period
        3. Get any undistributed surplus

        """

        company_list = []

        company = self.env.company
        if company.child_ids:
            company_list = [x.id for x in company.childs_ids]
            company_list.append(company.id)
        else:
            company_list = company.id

        self.env.cr.execute(
            """
            select aa.code_store, date_part('month', aml.date) as month, date_part('year', aml.date) as year, sum(aml.debit - aml.credit) as sum_balance, 'PL'
            from account_move_line aml
            join account_account aa on aml.account_id = aa.id
            join account_move am on aml.move_id = am.id
            where ( aa.account_type like 'income_%%' or aa.account_type like 'expense_%%' or aa.account_type is null) 
            and am.state = 'posted'
            and aml.date >= %(start_date)s
            and aml.date <= %(end_date)s
            and aml.company_id in (%(company_list)s)
            group by aa.code_store, date_part('month', aml.date), date_part('year',aml.date)
            order by aa.code_store, date_part('year',aml.date),  date_part('month', aml.date)
            """,
            {
                "start_date": self.from_date,
                "end_date": self.as_at_date,
                "company_list": company_list
            })

        res = self.env.cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))

        self.env.cr.execute(
            """
            select aa.code_store, date_part('month', aml.date) as month, date_part('year', aml.date) as year, sum(aml.debit - aml.credit) as sum_balance, 'BS'
            from account_move_line aml
            join account_account aa on aml.account_id = aa.id
            join account_move am on aml.move_id = am.id
            where (aa.account_type not like 'income_%%' and aa.account_type not like 'expense_%%')
            and am.state = 'posted'
            and aml.date <= %(end_date)s
            and aml.company_id in (%(company_list)s)
            group by aa.code_store, date_part('month', aml.date), date_part('year',aml.date)
            order by aa.code_store,date_part('year',aml.date),date_part('month', aml.date)
            """,
            {
                "end_date": self.as_at_date,
                "company_list": company_list
            })
        res = self.env.cr.fetchall()
        for line in res:
            rows.append(list(line))

        self.env.cr.execute(
            """
            select 'Undistributed Surplus' as name, date_part('month', aml.date) as month, date_part('year', aml.date) as year, sum(aml.debit - aml.credit) as sum_balance, 'US'
            from account_move_line aml
            join account_account aa on aml.account_id = aa.id
            join account_move am on aml.move_id = am.id
            where (aa.account_type like 'income_%%' or aa.account_type like 'expense_%%') 
            and am.state = 'posted'
            and aml.date<= %(end_date)s
            and aml.company_id in (%(company_list)s)
            group by date_part('month', aml.date), date_part('year',aml.date)
            order by date_part('year',aml.date), date_part('month', aml.date)
            """,
            {
                "end_date": self.as_at_date,
                "company_list": company_list
            })

        res = self.env.cr.fetchall()

        for line in res:
            rows.append(list(line))

        return rows

    def button_process(self):
        """ Create the report"""
        wizard_item = self[0]
        data = StringIO()

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')

        current_date = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), '%Y-%m-%d %H:%M:%S')
        start_date = self.from_date
        end_date = self.as_at_date
        number_of_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
        row_headings = []
        month = start_date.month
        year = start_date.year
        if month < 12:
            start_period = int(str(year) + '0' + str(month))
        else:
            start_period = int(str(year) + str(month))

        for i in range(0, number_of_months):
            if month < 10:
                month_string = '0' + str(month)
            else:
                month_string = str(month)
            row_headings.append(str(year) + month_string)
            month += 1
            if month > 12:
                month = 1
                year += 1

        row_headings_integer = []
        for row in row_headings:
            row_headings_integer.append(int(row))

        row = 1

        worksheet.write(row, 0, self.env.company.name)
        row += 1
        worksheet.write(row, 0, current_date)
        row += 1
        worksheet.write(row, 0, 'Trial Balance by Month Report as at ' + str(self.as_at_date))
        row += 2

        # write headings
        worksheet.write(row, 0, 'Code')
        for i in range(0, number_of_months):
            row_heading = row_headings[i]
            worksheet.write(row, i + 1, row_heading)

        process_dict = {}

        accounts = self.env['account.account'].search(['|', ('active', '=', False), ('active', '=', True)])
        for account in accounts:
            if account.include_initial_balance:
                line_type = 'BS'
            else:
                line_type = 'PL'
            for heading in row_headings:
                process_dict[account.code + '^' + heading] = (0, line_type)

        row_data = []
        row_data = self._get_rows_account()

        for item in row_data:
            year = str(int(item[2]))
            month = int(item[1])
            if month < 10:
                month_string = '0' + str(month)
            else:
                month_string = str(month)
            if isinstance(item[0], dict):
                k = list(item[0].values())[0]+ '^' + year + month_string
            else:
                k = ''+ '^' + year + month_string
            process_dict[k] = item[3], item[4]

        balance = 0
        this_account = False
        for k, v in sorted(process_dict.items()):
            separator = k.find('^')
            account = k[0:separator]
            period = k[separator + 1:len(k)]
            line_type = v[1]
            period_int = int(period)
            if line_type == 'US':
                period_int += 1
                month = str(period_int)[-2:]
                if int(month) == 13:
                    period_int += 88

            if account != this_account:
                row += 1
                balance = 0
                us_balance = 0
                this_account = account
            if period_int < start_period:
                if line_type in ('BS', 'US'):
                    balance += v[0]
                    us_balance += v[0]
                continue
            else:
                if line_type == 'BS':
                    balance += v[0]
                elif line_type == 'US':
                    balance = us_balance
                    us_balance += v[0]
                else:
                    balance = v[0]

            for i in range(0, number_of_months):
                if period == row_headings[i]:
                    column = i + 1
                    continue
            if account.isdigit():
                account = int(account)

            worksheet.write(row, 0, account)
            worksheet.write(row, column, balance)

        format_number = workbook.add_format({'num_format': '0.00', 'align': 'right'})
        format_row = workbook.add_format({'bold': True})
        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:Z', 10, format_number)
        workbook.close()
        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write({'data': output})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.trial.balance.month.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard_item.id,
            'target': 'new',
        }
