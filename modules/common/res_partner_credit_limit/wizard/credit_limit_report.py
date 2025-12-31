# -*- coding: utf-8 -*-
import base64
from io import BytesIO

import xlsxwriter

from odoo import models, fields


class CreditLimitReport(models.TransientModel):
    _name = "credit.limit.report"
    _description = "Credit Limit Report"

    ###########################################################################
    # Fields
    ###########################################################################
    export_xls = fields.Binary(string="Export file", readonly=True)
    report_name = fields.Char(string="Export file name", readonly=True, default="credit_limit_report.xls")
    done = fields.Boolean("Generated", default=False)

    def generate_report(self):
        report_data = self._generate_report_data()
        output = self._encode_report_data(report_data=report_data)
        self.write(
            {
                "export_xls": output,
                "done": True,
            })

        return {
            "name": "Credit Limit Report",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "view_id": False,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "new",
            "domain": "[]",
        }

    def _encode_report_data(self, report_data):
        fieldnames = [
            "ref",
            "customer",
            "credit_limit",
            "current_credit_status",
            "allow_over_credit",
        ]

        # Prepare file name
        report_name = "Over Credit Report {}".format(fields.Date.context_today(self))
        self.report_name = "{0}.xlsx".format(report_name)

        # Prepare xlsx file with a worksheet
        data = BytesIO()
        workbook = xlsxwriter.Workbook(data, {"in_memory": True})
        worksheet = workbook.add_worksheet("CreditLimitReport")

        # Formatting
        worksheet.set_column("A:C", 15)
        worksheet.set_column("C:F", 20)

        format_header = workbook.add_format({
            "text_wrap": True,
            "bold": True,
            "bg_color": "#7BBDC4",
            "border": 1
        })

        columns_map = {
            0: "Customer Code",
            1: "Customer",
            2: "Credit Limit",
            3: "Current Credit Status",
            4: "Allow Over Credit Ticked",
        }

        # Write report header
        row = 1

        for key, value in columns_map.items():
            worksheet.write(row, key, value, format_header)

        row += 1

        # Write report body
        for report_data_line in report_data:
            for index, field_name in enumerate(fieldnames):
                worksheet.write(row, index, report_data_line[field_name])
            row += 1

        workbook.close()
        data.seek(0)
        output = base64.b64encode(data.read()).decode()
        return output

    def _get_customers(self):
        return self.env["res.partner"].search(
            [
                ("customer_rank", ">", 0),
                ("is_company", "=", True),
                ("active", "=", True),
            ])

    def _generate_report_data(self):
        data = []
        customers = self._get_customers()
        for customer in customers:
            data.append(
                {
                    "ref": customer.ref,
                    "customer": customer.name,
                    "current_credit_status": round(customer.total_receivable, 2),
                    "credit_limit": customer.credit_limit,
                    "allow_over_credit": "true" if customer.over_credit else "",
                })

        return data
