# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlsxwriter

from odoo import models, fields


def chunk_list(big_list, chunk_size):
    """
    Yield successive chunks from a list.
    Ref: http://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    Args:
        big_list: big list of items.
        chunk_size: number of items in each chunk max.
    Returns:
        A list representing the next chunk of big_list.
    """
    for i in range(0, len(big_list), chunk_size):
        yield big_list[i:i + chunk_size]


class UnallocatedCashReport(models.TransientModel):
    """
    Unallocated Cash Report
    """
    _name = "unallocated.cash.report"
    _description = __doc__

    # Fields
    report_name = fields.Char(size=64, string="Report Name", readonly=True, default="Unallocated Cash Report.xlsx")
    data = fields.Binary(string="Download File", readonly=True)
    state = fields.Selection(selection=[
        ("draft", "Draft"),
        ("done", "Done"),
    ], default="draft", string="State", required=True)

    def button_process(self):
        """
        Create the report
        """
        data = BytesIO()

        workbook = xlsxwriter.Workbook(data, {"in_memory": True})
        worksheet = workbook.add_worksheet("Data")

        # write headings
        worksheet.write(0, 0, "Type")
        worksheet.write(0, 1, "Customer")
        worksheet.write(0, 2, "Customer Number")
        worksheet.write(0, 3, "Invoice Number")
        worksheet.write(0, 4, "Line Total")
        worksheet.write(0, 5, "Line Balance")

        row = 1

        move_lines = self.env["account.move.line"].search(
            [
                ("partner_id", "!=", False),
                ("account_id.account_type", "=", "asset_receivable"),
                ("credit", ">", 0.0),
                ("reconciled", "=", False),
                ('parent_state','=', 'posted'),
            ])
        for chunk_ids in chunk_list(move_lines, 100):
            for account_move_line in chunk_ids:
                title = "receipt" if account_move_line.statement_line_id else "credit-note"
                worksheet.write(row, 0, title)
                worksheet.write(row, 1, account_move_line.partner_id.name)
                worksheet.write(row, 2, account_move_line.partner_id.ref or '')
                worksheet.write(row, 3, account_move_line.name or '')
                worksheet.write(row, 4, account_move_line.credit)
                worksheet.write(row, 5, account_move_line.balance)
                row += 1

        format_number = workbook.add_format({"num_format": "0.00", "align": "right"})
        format_row = workbook.add_format({"text_wrap": True, "bold": True})
        worksheet.set_row(0, 20, format_row)
        worksheet.set_column("A:A", 25)
        worksheet.set_column("B:D", 30)
        worksheet.set_column("C:C", 35)
        worksheet.set_column("E:F", 15, format_number)
        workbook.close()
        data.seek(0)
        output = base64.b64encode(data.read()).decode()
        self.write(
            {
                "data": output,
                "state": "done",
            })

        return {
            "type": "ir.actions.act_window",
            "res_model": "unallocated.cash.report",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "target": "new",
        }
