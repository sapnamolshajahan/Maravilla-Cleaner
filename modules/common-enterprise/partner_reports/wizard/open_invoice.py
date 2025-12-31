# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from io import BytesIO as StringIO

import xlsxwriter

from odoo import models, fields


class PartnerOpenInvoice(models.TransientModel):
    _name = 'res.partner.open.invoice'
    _description = 'Partner Open Invoices'

    report_name = fields.Char(size=64, string='Report Name', readonly=True, default='Open Invoices Report')
    data = fields.Binary(string='Download File', readonly=True)
    type = fields.Selection(selection=[("asset_receivable", "Receivables"), ("liability_payable", "Payables")], string="Type",
                            default="asset_receivable", required=True)

    def button_process(self):
        """ Create the report"""

        wizard_item = self[0]
        report_date = fields.Date.context_today(self)
        report_name = 'Open Invoices Report as at ' + fields.Date.to_string(report_date)

        # now do standard XLSX output
        self.write({'report_name': self.report_name + '.xlsx'})
        data = StringIO()

        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')

        current_date = datetime.strftime(fields.Datetime.context_timestamp(self, datetime.now()), '%d-%m-%Y %H:%M:%S')

        cell_left = workbook.add_format({'align': 'left'})
        cell_right_numeric = workbook.add_format({'align': 'right', 'num_format': '0.00', })
        cell_bold = workbook.add_format({'bold': True})
        cell_date = workbook.add_format({'num_format': 'dd/mm/yy'})
        row = 1

        worksheet.write(row, 0, self.env.company.name, cell_bold)
        row += 1
        worksheet.write(row, 0, 'Run Date: ' + current_date, cell_bold)
        row += 1
        worksheet.write(row, 0, report_name, cell_bold)
        row += 1

        # write headings
        worksheet.write(row, 0, 'Code', cell_left)
        worksheet.write(row, 1, 'Name', cell_left)
        worksheet.write(row, 2, 'Due Date', cell_right_numeric)
        worksheet.write(row, 3, 'Amount', cell_right_numeric)
        row += 1

        sql_string = """
                    select res.ref, res.name, aml.date, sum(aml.debit-aml.credit) 
                    from account_move_line aml 
                    left join res_partner res on aml.partner_id = res.id
                    left join account_account aa on aml.account_id = aa.id  
                    where aa.account_type = '{type}' 
                    and aml.company_id = {company} 
                    group by res.ref, res.name,aml.date  
                    having sum(aml.debit-aml.credit) != 0 
                    order by res.name, aml.date
                    """

        sql_string = sql_string.format(type=self.type,
                                       company=self.env.company.id)
        self.env.cr.execute(sql_string)
        res = self.env.cr.fetchall()

        for item in res:
            if item[0]:
                code = item[0]
            else:
                code = ' '
            worksheet.write(row, 0, code)
            worksheet.write(row, 1, item[1])
            worksheet.write(row, 2, item[2], cell_date)
            worksheet.write(row, 3, item[3], cell_right_numeric)
            row += 1

        row += 2

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:D', 15)
        workbook.close()
        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write({'data': output})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.open.invoice',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard_item.id,
            'target': 'new',
        }
