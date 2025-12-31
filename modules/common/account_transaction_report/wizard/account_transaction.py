# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from io import BytesIO

import xlsxwriter

from odoo import models, fields
from odoo.exceptions import UserError


class AccountTransactionReport(models.TransientModel):
    """
    Account Transaction Export"
    """
    _name = "account.transaction.report"
    _description = __doc__

    def _report_name(self):
        report_date = datetime.strftime(fields.Date.context_today(self), "%d-%m-%Y")
        return "General Ledger Transactions Report {}.xlsx".format(report_date)

    ################################################################################
    # Fields
    ################################################################################
    from_date = fields.Date(string="From Date", default=fields.Date.today(), required=True)
    to_date = fields.Date(string="To Date", default=fields.Date.today(), required=True)
    accounts = fields.Many2many("account.account", string="Accounts")
    tags = fields.Many2many('account.account.tag', string='Tags')
    state = fields.Selection(
        [
            ("init", "Setup"),
            ("done", "Done")
        ], default="init", string="State", required=True)
    report_name = fields.Char(string="Report Name", readonly=True, default=_report_name)
    data = fields.Binary(string="Download File", readonly=True)

    def _get_account_year(self):
        """
        Calculate start and end date of the current accounting year
        :return: start and end date strings
        """
        today = self.from_date
        fiscal_last_month = int(self.env.company.fiscalyear_last_month)

        # Need to calculate accounting year here
        if today.month <= fiscal_last_month:
            start_year = today.year - 1
        else:
            start_year = today.year

        start_date_str = '{year}-{month}-01'.format(year=start_year, month=fiscal_last_month + 1)

        return start_date_str

    def _get_rows_account(self, account, start_date):

        sql_select = """
            select aml.date, aml.debit, aml.credit, aml.name, aml.ref,aml.partner_id, aml.product_id, am.name
            from account_move_line aml
            join account_move am on aml.move_id = am.id 
            where aml.account_id = {account}
            and aml.date >= '{start_date}'
            and aml.date <= '{end_date}' 
            and (aml.debit != 0.0 or aml.credit != 0.0) 
            and aml.parent_state = 'posted' 
            order by aml.date asc"""
        self.env.cr.execute(sql_select.format(account=account.id, start_date=start_date, end_date=self.to_date))

        res = self.env.cr.fetchall()
        rows = []
        for line in res:
            line = list(line)
            rows.append(line)

        return rows

    def calc_opening_balance(self, account, start_date):
        """
        include_initial_balance = True  = balance sheet, so we want everything from day 0 to start of report as opening balance.
        include_initial_balance = False or null = expense, so gets transactions from start of fiscal year to start of report
        """
        if account.include_initial_balance:
            opening_balance_sql = """
                        select sum (debit-credit)
                        from account_move_line
                        where account_id = {account}
                         and parent_state = 'posted' 
                        and date < '{start_date}'"""
            self.env.cr.execute(opening_balance_sql.format(account=account.id, start_date=start_date))
        else:
            year_start_date = self._get_account_year()  # returns a string
            opening_balance_sql = """
                                    select sum (debit-credit)
                                    from account_move_line
                                    where account_id = {account}
                                     and parent_state = 'posted' 
                                    and date < '{start_date}' and date >= '{year_start_date}'"""
            self.env.cr.execute(
                opening_balance_sql.format(account=account.id, start_date=start_date, year_start_date=year_start_date))
        return self.env.cr.fetchall()[0][0] or 0

    def get_accounts(self):

        account_list = []

        if self.accounts:
            account_list.extend([x.id for x in self.accounts])

        if self.tags:
            accounts = self.env['account.account'].search([('tag_ids', 'in', [x.id for x in self.tags])])
            account_list.extend([x.id for x in accounts])

        account_list = list(set(account_list))
        return account_list

    def button_process(self):
        """
        Create the report
        """
        self.ensure_one()
        if not self.accounts:
            raise UserError("Must specify an account.")

        # now do standard XLSX output
        data = BytesIO()

        workbook = xlsxwriter.Workbook(data, {"in_memory": True})
        worksheet = workbook.add_worksheet("Data")

        current_date = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), "%d-%m-%Y %H:%M:%S")

        cell_left = workbook.add_format({"align": "left"})
        cell_left_bold = workbook.add_format({"align": "left", "bold": True})
        cell_right_bold = workbook.add_format({"align": "right", "bold": True})
        cell_right = workbook.add_format({"align": "right"})
        cell_right_numeric = workbook.add_format({"align": "right", "num_format": "0.00", })
        row = 1

        from_date = datetime.strftime(self.from_date, "%d-%m-%Y")
        to_date = datetime.strftime(self.to_date, "%d-%m-%Y")

        headings = ["Company", "Run Date", "From Date", "To Date"]
        headings_data = [self.env.company.name, current_date, from_date, to_date]
        for i in range(0, len(headings)):
            worksheet.write(row, 0, headings[i])
            worksheet.write(row, 1, headings_data[i])
            row += 1

        row += 1

        worksheet.write(row, 0, "Date", cell_right_bold)
        worksheet.write(row, 1, "Move", cell_right_bold)
        worksheet.write(row, 2, "Description", cell_left_bold)
        worksheet.write(row, 3, "Partner", cell_left_bold)
        worksheet.write(row, 4, "Product", cell_left_bold)
        worksheet.write(row, 5, "Debit", cell_right_bold)
        worksheet.write(row, 6, "Credit", cell_right_bold)
        worksheet.write(row, 7, "Balance", cell_right_bold)

        row += 2

        account_list = self.get_accounts()
        accounts = self.env["account.account"].search([("id", "in", account_list)], order="code")

        for account in accounts:
            opening_balance = self.calc_opening_balance(account, self.from_date)
            row_data = self._get_rows_account(account, self.from_date)
            closing_balance = opening_balance

            worksheet.write(row, 0, account.code, cell_left_bold)
            worksheet.write(row, 1, account.name, cell_left_bold)
            row += 1
            worksheet.write(row, 1, "Opening Balance", cell_left_bold)
            worksheet.write(row, 6, opening_balance, cell_right_numeric)
            row += 1

            for item in row_data:
                if item[5]:
                    partner_name = self.env["res.partner"].browse(item[5]).name
                else:
                    partner_name = ""
                if item[6]:
                    product = self.env["product.product"].browse(item[6])
                    product_name = product.product_tmpl_id.name
                else:
                    product_name = ""
                worksheet.write(row, 0, item[0], cell_right)
                worksheet.write(row, 1, item[7], cell_left)
                worksheet.write(row, 2, str(item[3]) + " " + str(item[4]), cell_left)
                worksheet.write(row, 3, partner_name, cell_left)
                worksheet.write(row, 4, product_name, cell_left)
                worksheet.write(row, 5, item[1], cell_right_numeric)
                worksheet.write(row, 6, item[2], cell_right_numeric)
                worksheet.write(row, 7, item[1] - item[2], cell_right_numeric)
                row += 1
                closing_balance += item[1] - item[2]

            worksheet.write(row, 1, "Closing Balance", cell_left_bold)
            worksheet.write(row, 6, closing_balance, cell_right_numeric)

            row += 2

        worksheet.set_column("A:B", 10)
        worksheet.set_column("C:E", 50)
        worksheet.set_column("F:H", 15)
        workbook.close()
        data.seek(0)
        self.write(
            {
                "data": base64.encodebytes(data.read()),
                "state": "done",
            })

        return {
            "name": "Report Result",
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
