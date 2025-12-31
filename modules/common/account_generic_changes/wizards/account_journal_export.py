# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlsxwriter

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountJournalExport(models.TransientModel):
    """
    Account Journal Export"
    """
    _name = "account.journal.export"
    _description = __doc__

    @api.depends('move_id')
    def _report_name(self):
        return "Journal Report {}.xlsx".format(self.move_id.name if self.move_id.name else 'Draft Journal')

    ################################################################################
    # Fields
    ################################################################################
    move_id = fields.Many2one('account.move', string='Move')
    report_name = fields.Char(string="Report Name", readonly=True, default=_report_name)
    data = fields.Binary(string="Download File", readonly=True)

    def button_process(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError("Must select a journal.")

        # now do standard XLSX output
        data = BytesIO()

        workbook = xlsxwriter.Workbook(data, {"in_memory": True})
        worksheet = workbook.add_worksheet("Data")

        cell_left = workbook.add_format({"align": "left"})
        cell_left_bold = workbook.add_format({"align": "left", "bold": True})
        cell_right_bold = workbook.add_format({"align": "right", "bold": True})
        cell_right = workbook.add_format({"align": "right"})
        cell_right_numeric = workbook.add_format({"align": "right", "num_format": "0.00", })
        row = 1
        worksheet.write(row, 0, 'Date', cell_right_bold)
        worksheet.write(row, 1, 'Name', cell_left_bold)
        worksheet.write(row, 2, 'Ref', cell_left_bold)
        worksheet.write(row, 3, 'Partner', cell_left_bold)
        worksheet.write(row, 4, 'Code', cell_left_bold)
        worksheet.write(row, 5, 'Account', cell_left_bold)
        worksheet.write(row, 6, 'Debit', cell_right_bold)
        worksheet.write(row, 7, 'Credit', cell_right_bold)
        worksheet.write(row, 8, 'Currency', cell_left_bold)
        worksheet.write(row, 9, 'Curr Amount', cell_right_bold)
        row += 1

        lines = self.move_id.line_ids
        for line in lines.filtered(lambda x: x.account_id):
            worksheet.write(row, 0, line.date, cell_right)
            worksheet.write(row, 1, line.name, cell_left)
            worksheet.write(row, 2, line.ref, cell_left)
            worksheet.write(row, 3, line.partner_id.name, cell_left)
            worksheet.write(row, 4, line.account_id.code, cell_left)
            worksheet.write(row, 5, line.account_id.name, cell_left)
            worksheet.write(row, 6, line.debit, cell_right_numeric)
            worksheet.write(row, 7, line.credit, cell_right_numeric)
            worksheet.write(row, 8, line.currency_id.name, cell_left)
            worksheet.write(row, 9, line.amount_currency, cell_right_numeric)
            row += 1

        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:D", 40)
        worksheet.set_column("E:H", 15)
        workbook.close()
        data.seek(0)
        self.write({"data": base64.encodebytes(data.read())})

        return {
            "name": "Report Result",
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
