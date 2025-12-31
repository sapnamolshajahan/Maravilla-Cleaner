# -*- coding: utf-8 -*-
from decimal import Decimal
from io import BytesIO as StringIO

import xlsxwriter

from odoo import models, fields, api


class ARAPAuditReport(models.TransientModel):
    """ AR & AP Audit Report to XLS
    """
    _name = 'ar.ap.audit.xls.report'
    _description = 'Ar and AP Audit Report'

    # Fields

    name = fields.Char(string="Unused")

    def run_report(self, wizard):
        """ Create the report.
        """
        report_name = "AR & AP Audit Report"
        file_name = "{0}.xlsx".format(report_name)

        data = StringIO()
        workbook = xlsxwriter.Workbook(data)
        worksheet = workbook.add_worksheet('Data')

        row = 0

        # write report header
        period = wizard.as_at_date
        worksheet.write(row, 0, 'AR AP Audit Report as at: ' + str(period))
        if wizard.statement_currency:
            worksheet.write(row, 0, 'Currency: ' + wizard.statement_currency.name)
        else:
            worksheet.write(row, 0, 'Currency: None')

        row += 2

        # write headings
        worksheet.write(row, 0, 'Code')
        worksheet.write(row, 1, 'Name')
        worksheet.write(row, 2, 'Balance')
        worksheet.write(row, 3, 'GL Balance')
        worksheet.write(row, 4, 'Difference')

        row += 2

        # now select the records
        lines = self.env["res.partner.statement.lines"].search(
            [
                ('res_partner_statement_id', '=', wizard.id)
            ])

        dict_of_differences = self.local_currency_report(lines, wizard)
        workbook = self.write_xls_lines(dict_of_differences, worksheet, workbook, row, wizard)
        format_number = workbook.add_format({'num_format': '0.00', 'align': 'right'})

        worksheet.set_column('B:B', 50, )
        worksheet.set_column('C:H', 10, format_number)

        workbook.close()

        return (report_name, file_name, "ATB Detail Report", data)

    @api.model
    def round_dp(self, value_to_round, number_of_decimals):
        if number_of_decimals and value_to_round:
            TWO_PLACES = Decimal(10) ** -number_of_decimals
            return float(Decimal(str(value_to_round)).quantize(TWO_PLACES))
        return False

    def write_xls_lines(self, dict_of_differences, worksheet, workbook, row, wizard):
        for v in dict_of_differences.values():
            worksheet.write(row, 0, v[0])
            worksheet.write(row, 1, v[1])
            worksheet.write(row, 2, v[2])
            worksheet.write(row, 3, v[3])
            worksheet.write(row, 4, v[4])
            row += 1

        return workbook

    def local_currency_report(self, lines, wizard):
        for line in lines:

            if not line.sort_name:
                line.sort_name = 'Unknown'

            if not line.transaction_partner_id:
                line.transaction_partner_id = self.env.company.partner_id.id

        sorted_lines = sorted(lines, key=lambda x: (x.sort_name, x.transaction_partner_id.id))
        accounts = self.env['account.account'].search([('account_type', 'in', ('asset_receivable', 'liability_payable'))])
        search_accounts = [x.id for x in accounts]

        current_partner = sorted_lines[0].transaction_partner_id.id or False
        ref = sorted_lines[0].transaction_partner_id.ref
        name = sorted_lines[0].sort_name
        accum_balance = 0.0
        line_count = 0
        dict_of_differences = {}

        for line in sorted_lines:
            line_count += 1
            if line.transaction_partner_id.id == current_partner:
                accum_balance += line.balance
                if line_count != len(sorted_lines):
                    continue
            if current_partner:
                sql_query = """ select sum(debit-credit) from account_move_line where partner_id = {partner_id} 
                                and account_id in {account} and parent_state = 'posted' and date <= '{date}'
                            """.format(partner_id=current_partner,
                                         account=tuple([x for x in search_accounts]),
                                         date=wizard.as_at_date)

            else:
                sql_query = """ select sum(debit-credit) from account_move_line where partner_id is null 
                                                and account_id in {account} and parent_state = 'posted' and date <= '{date}'
                                            """.format(account=tuple([x for x in search_accounts]),
                                                       date=wizard.as_at_date)
            try:
                self.env.cr.execute(sql_query)
            except:
                pass
            gl_lines = self.env.cr.fetchall()
            gl_balance = 0.0
            if gl_lines:
                try:
                    gl_balance = gl_lines[0][0]
                except:
                    pass

            try:
                difference = self.round_dp(accum_balance - gl_balance, 2)
            except:
                difference = accum_balance

            if difference and abs(difference) > 0.005:
                dict_of_differences[line.transaction_partner_id.id] = [ref, name, accum_balance, gl_balance, difference]

            accum_balance = line.balance
            ref = line.transaction_partner_id.ref
            name = line.sort_name
            current_partner = line.transaction_partner_id.id
        # now check if we have any GL partner accounts that are not on the report

        list_of_report_partners = list(set([x.transaction_partner_id.id for x in sorted_lines if x.transaction_partner_id]))
        sql_query = """select partner_id from account_move_line where partner_id is not null and partner_id not in {partners} 
                        and account_id in {accounts} and parent_state = 'posted' and date <= '{date}' 
                        group by partner_id having abs(sum(debit)-sum(credit)) > 0.005
                    """.format(partners=tuple([x for x in list_of_report_partners]),
                               accounts=tuple([x for x in search_accounts]),
                               date=wizard.as_at_date)
        try:
            result = self.env.cr.fetchall()
            missing_partners = [x[0] for x in result] if result else []
        except:
            # Handle the case where no results are available to fetch
            missing_partners = []

        for partner in missing_partners:
            dict_of_differences[partner] = ['Should have a balance', partner, 0, 0, 0]

        return dict_of_differences
