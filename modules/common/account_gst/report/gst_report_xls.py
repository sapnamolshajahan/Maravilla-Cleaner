# -*- coding: utf-8 -*-

import logging
from io import BytesIO as StringIO

_logger = logging.getLogger(__name__)

import xlsxwriter

from odoo import models, fields


class AccountGSTXlsReport(models.TransientModel):
    """ GST Report XLS
    """
    _name = "account.gst.xls.report"
    _description = 'GST report XLS'

    ###########################################################################
    #
    # - Fields
    #
    ###########################################################################

    name = fields.Char(string="Unused")

    def write_invoice_line(self, line, value_excl, gst, value_incl, row, worksheet, gst_type, cell_right_numeric,
                           cell_right):
        worksheet.write(row, 0, fields.Date.to_string(line.date))
        worksheet.write(row, 1, line.invoice_number)
        worksheet.write(row, 2, line.ref)
        worksheet.write(row, 3, value_excl, cell_right_numeric)
        worksheet.write(row, 4, gst, cell_right_numeric)
        worksheet.write(row, 5, value_incl, cell_right_numeric)
        worksheet.write(row, 6, line.move_id_technical, cell_right)
        worksheet.write(row, 7, line.move_id.partner_id.name or line.partner_id.name)

        return row

    def write_subtotal_line(self, value_excl, gst, value_incl, row, worksheet, gst_type, cell_right_numeric,
                            cell_right):
        row += 1
        worksheet.write(row, 3, value_excl, cell_right_numeric)
        worksheet.write(row, 4, gst, cell_right_numeric)
        worksheet.write(row, 5, value_incl, cell_right_numeric)
        row += 2
        if not gst_type:
            gst_type = 'Other Transactions'
        worksheet.write(row, 0, gst_type)
        row += 2
        return (row)

    def total_block(self, lines, row, worksheet, wizard, cell_right_numeric, cell_right):

        row += 2
        worksheet.write(row, 1, "Summary Section")
        worksheet.write(row, 3, "Value Excl", cell_right)
        worksheet.write(row, 4, "GST", cell_right)
        worksheet.write(row, 5, "Value Incl", cell_right)

        if not lines:
            return

        total_value_excl = 0.0
        total_gst = 0.0
        total_value_incl = 0.0

        row += 1

        tax_types = ['sale', 'purchase', 'other']

        for i in range(0, len(tax_types)):
            row += 1
            tax_type = tax_types[i]
            worksheet.write(row, 1, tax_type)

            taxes = self.env['account.tax'].search([('type_tax_use','=', tax_type)])
            for tax in taxes:
                tax_lines = lines.filtered(lambda x: x.account_tax_id.id == tax.id)
                if not tax_lines:
                    value_excl = 0.0
                    gst = 0.0
                    value_incl = 0.0
                else:
                    value_excl = sum([x.value_excl for x in tax_lines])
                    gst = sum([x.gst for x in tax_lines])
                    value_incl = sum([x.value_incl for x in tax_lines])
                    total_value_excl += value_excl
                    total_gst += gst
                    total_value_incl += value_incl
                worksheet.write(row, 2, tax.name)
                worksheet.write(row, 3, value_excl, cell_right_numeric)
                worksheet.write(row, 4, gst, cell_right_numeric)
                worksheet.write(row, 5, value_incl, cell_right_numeric)
                row+=1

        row += 1
        worksheet.write(row, 1, 'Other')
        row += 1
        tax_lines = lines.filtered(lambda x: not x.account_tax_id)
        if not tax_lines:
            value_excl = 0.0
            gst = 0.0
            value_incl = 0.0
        else:
            value_excl = sum([x.value_excl for x in tax_lines])
            gst = sum([x.gst for x in tax_lines])
            value_incl = sum([x.value_incl for x in tax_lines])
            total_value_excl += value_excl
            total_gst += gst
            total_value_incl += value_incl
        worksheet.write(row, 2, 'Other Transactions')
        worksheet.write(row, 3, value_excl, cell_right_numeric)
        worksheet.write(row, 4, gst, cell_right_numeric)
        worksheet.write(row, 5, value_incl, cell_right_numeric)

        row += 1
        worksheet.write(row, 2, "Total")
        worksheet.write(row, 3, total_value_excl, cell_right_numeric)
        worksheet.write(row, 4, total_gst, cell_right_numeric)
        worksheet.write(row, 5, total_value_incl, cell_right_numeric)

        # now add the GL movement for comparison purposes

        row += 2
        worksheet.write(row, 1, "GL Movement")
        total_gst = 0.0
        for account in wizard.account_ids:
            move_lines = self.env['account.move.line'].search([('account_id', '=', account.id),
                                                               ('date', '>=', wizard.from_date),
                                                               ('date', '<=', wizard.to_date),
                                                               ('move_id.state', '=', 'posted')])
            gst = round(sum([x.debit - x.credit for x in move_lines]), 2)
            worksheet.write(row, 2, account.name)
            worksheet.write(row, 3, gst, cell_right_numeric)
            row += 1
            total_gst += gst
        worksheet.write(row, 2, "Nett")
        worksheet.write(row, 3, total_gst, cell_right_numeric)

        row += 2
        worksheet.write(row, 1, "GL Balances")
        total_gst = 0.0
        for account in wizard.account_ids:
            sql_select = \
                """
                   select sum(debit-credit) from account_move_line where account_id = {account} and date <= '{to_date}' and parent_state = 'posted'  
                """
            self.env.cr.execute(sql_select.format(account=account.id,
                                                  to_date=wizard.to_date))
            account_gst = self.env.cr.fetchall()
            if account_gst and account_gst[0] and account_gst[0][0]:
                gst = round(account_gst[0][0], 2)
                worksheet.write(row, 2, account.name)
                worksheet.write(row, 3, gst, cell_right_numeric)
                row += 1
                total_gst += gst
        worksheet.write(row, 2, "Balance")
        worksheet.write(row, 3, total_gst, cell_right_numeric)


    def detail_report(self, lines, row, worksheet, cell_right_numeric, cell_right):
        if not lines:
            return row

        tax_type = lines[0].gst_type
        # write the first gst type
        worksheet.write(row, 0, tax_type)
        amount_excl_gst = 0.0
        gst = 0.0
        amount_incl_gst = 0.0
        row += 2
        for line in lines:
            if line.gst_type != tax_type:
                row = self.write_subtotal_line(amount_excl_gst, gst, amount_incl_gst, row, worksheet, line.gst_type,
                                               cell_right_numeric, cell_right)
                amount_excl_gst = 0.0
                gst = 0.0
                amount_incl_gst = 0.0
                row += 1
                tax_type = line.gst_type
            worksheet.write(row, 0, fields.Date.to_string(line.date))
            worksheet.write(row, 1, line.invoice_number)
            worksheet.write(row, 2, line.ref)
            worksheet.write(row, 3, line.value_excl, cell_right_numeric)
            worksheet.write(row, 4, line.gst, cell_right_numeric)
            worksheet.write(row, 5, line.value_incl, cell_right_numeric)
            worksheet.write(row, 6, line.account_id.name)
            amount_excl_gst += line.value_excl
            gst += line.gst
            amount_incl_gst += line.value_incl
            row += 1

        # write the last sub-total
        row = self.write_subtotal_line(amount_excl_gst, gst, amount_incl_gst, row, worksheet, line.gst_type,
                                       cell_right_numeric, cell_right)

        return row

    def summary_report(self, lines, row, worksheet, cell_right_numeric, cell_right):
        if not lines:
            return row

        tax_type = lines[0].gst_type
        # write the first gst type
        worksheet.write(row, 0, tax_type)

        # initialise variables
        amount_excl_gst = 0.0
        gst = 0.0
        amount_incl_gst = 0.0

        invoice_amount_excl_gst = 0.0
        invoice_gst = 0.0
        invoice_amount_incl_gst = 0.0

        row += 2
        tax_name = lines[0].account_tax_id.name if lines[0].account_tax_id else 'Not set'
        aggregation_code = str(lines[0].invoice_number) + str(lines[0].ref) + str(lines[0].account_id.name) + str(tax_name)

        previous_line = lines[0]

        for line in lines:
            tax_name = line.account_tax_id.name if line.account_tax_id else 'Not set'
            line_aggregation_code = str(line.invoice_number) + str(line.ref) + str(line.account_id.name) + str(tax_name)
            if (line_aggregation_code != aggregation_code) or \
                    (aggregation_code is False):
                row = self.write_invoice_line(
                    previous_line, invoice_amount_excl_gst, invoice_gst,
                    invoice_amount_incl_gst, row, worksheet, line.gst_type, cell_right_numeric, cell_right
                )
                aggregation_code = line_aggregation_code
                row += 1
                invoice_amount_excl_gst = 0.0
                invoice_gst = 0.0
                invoice_amount_incl_gst = 0.0

            if line.gst_type != tax_type:
                row = self.write_subtotal_line(amount_excl_gst, gst, amount_incl_gst,
                                               row, worksheet, line.gst_type, cell_right_numeric, cell_right)
                amount_excl_gst = 0.0
                gst = 0.0
                amount_incl_gst = 0.0
                row += 1
                tax_type = line.gst_type

            previous_line = line
            invoice_amount_excl_gst += line.value_excl
            invoice_gst += line.gst
            invoice_amount_incl_gst += line.value_incl
            amount_excl_gst += line.value_excl
            gst += line.gst
            amount_incl_gst += line.value_incl

        # deal with the last line
        row = self.write_invoice_line(line, invoice_amount_excl_gst,
                                      invoice_gst, invoice_amount_incl_gst, row,
                                      worksheet, line.gst_type, cell_right_numeric, cell_right)
        row += 1

        # write the last sub-total
        row = self.write_subtotal_line(amount_excl_gst, gst, amount_incl_gst,
                                       row, worksheet, line.gst_type, cell_right_numeric, cell_right)

        return row

    def run_report(self, wizard):
        """ Create the report.
        """
        report_name = "GST Report"
        file_name = "{0}.xlsx".format(report_name)

        data = StringIO()
        workbook = xlsxwriter.Workbook(data)
        worksheet = workbook.add_worksheet('Data')
        cell_right_numeric = workbook.add_format({'align': 'right', 'num_format': '0.00', })
        cell_right = workbook.add_format({'align': 'right'})
        row = 1

        # write report header
        if wizard.from_date and wizard.to_date:
            period_string = " from " + str(wizard.from_date) + ' to ' + str(wizard.to_date)
            worksheet.write(row, 0, 'GST Report for Dates ' + period_string)
        else:
            worksheet.write(row, 0, 'GST Report without Dates ')
        row += 1

        company = self.env.company.name
        worksheet.write(row, 0, 'Company:' + company)
        row += 2

        # write headings
        worksheet.write(row, 0, 'Date')
        worksheet.write(row, 1, 'Invoice#')
        worksheet.write(row, 2, 'Trans Ref')
        worksheet.write(row, 3, 'Excl GST', cell_right)
        worksheet.write(row, 4, 'GST', cell_right)
        worksheet.write(row, 5, 'Incl GST', cell_right)
        if wizard.detail == 'summary':
            worksheet.write(row, 6, 'Line Move ID (Technical)', cell_right)
        else:
            worksheet.write(row, 6, 'Line Description')
        worksheet.write(row, 7, 'Partner')

        row += 2

        # now select the records
        lines = self.env["account.gst.report.lines"].search(
            [
                ('account_gst_report_id', '=', wizard.id)
            ], order='gst_type,date,invoice_number,ref')

        if wizard.detail == 'summary':
            row = self.summary_report(lines, row, worksheet, cell_right_numeric, cell_right)
        else:
            row = self.detail_report(lines, row, worksheet, cell_right_numeric, cell_right)

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:G', 20)
        worksheet.set_column('H:H', 30)

        # now do summary section

        worksheet = workbook.add_worksheet('Summary')
        row = 1

        # write report header
        if wizard.from_date and wizard.to_date:
            period_string = " from " + fields.Date.to_string(wizard.from_date) + ' to ' + fields.Date.to_string(wizard.to_date)
            worksheet.write(row, 0, 'GST Report for Dates ' + period_string)
        else:
            worksheet.write(row, 0, 'GST Report without Dates ')
        row += 1

        company = self.env.company.name
        worksheet.write(row, 0, 'Company:' + company)
        row += 2

        self.total_block(lines, row, worksheet, wizard, cell_right_numeric, cell_right)
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:G', 20)
        worksheet.set_column('H:H', 30)

        workbook.close()

        return report_name, file_name, "GST Report", data
