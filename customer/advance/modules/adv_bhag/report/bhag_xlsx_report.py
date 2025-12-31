from odoo import models
from datetime import datetime


class BhagXlsxReport(models.AbstractModel):
    _name = 'report.adv_bhag.bhag_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizards):
        wizard = wizards[0]
        company = self.env.company

        title_format = workbook.add_format({
            'bold': True,
            'top': 1,
            'left': 1,
            'right': 1,
            'bg_color': '#D9D9D9',
            'font_size': 11,
            'align': 'center',
            'valign': 'vcenter'
        })
        sub_title_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9D9D9',
            'left': 1,
            'right': 1,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#D9D9D9',
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter'
        })
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'font_size': 10,
            'valign': 'vcenter'
        })
        qty_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'font_size': 10,
            'valign': 'vcenter'
        })

        sheet = workbook.add_worksheet("BHAG Report")
        sheet.set_column(1, 1, 35)
        sheet.set_column(2, 2, 15)
        start_row = 1
        start_col = 1
        sheet.merge_range(start_row, start_col, start_row, start_col + 1, company.name, title_format)
        sheet.merge_range(start_row + 1, start_col, start_row + 1, start_col + 1, "BHAG Report", sub_title_format)
        date_title = f"From: {wizard.date_from}   To: {wizard.date_to}"
        sheet.merge_range(start_row + 2, start_col, start_row + 2, start_col + 1, date_title, sub_title_format)
        header_row = start_row + 3
        sheet.set_row(header_row, 25)  # Bigger height for header row
        sheet.write(header_row, start_col, "Product Group", header_format)
        sheet.write(header_row, start_col + 1, "Quantity Sold", header_format)

        domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', wizard.date_from),
            ('order_id.date_order', '<=', wizard.date_to),
        ]
        sol = self.env['sale.order.line'].search(domain)
        results = {}
        for line in sol:
            tmpl = line.product_id.product_tmpl_id
            group = tmpl.product_group_id.name if tmpl.product_group_id else "No Group"
            qty = line.product_uom_qty
            results[group] = results.get(group, 0) + qty
            row = header_row + 1
            for group, qty in results.items():
                sheet.write(row, start_col, group, cell_format)
                sheet.write(row, start_col + 1, qty, qty_format)
                row += 1
