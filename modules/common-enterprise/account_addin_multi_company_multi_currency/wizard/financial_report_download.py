# -*- coding: utf-8 -*-
from xlsxwriter.utility import xl_rowcol_to_cell

from odoo import models
from .chart_type_builder import MCProfitLossBuilder


class AddinFinancialReportDownload(models.TransientModel):
    _inherit = "addin.financial.report.download"

    def get_chart_builder(self):

        if self.report_id.chart_id.type == "profit-loss":
            return MCProfitLossBuilder(self)
        return super(AddinFinancialReportDownload, self).get_chart_builder()

    def print_company_name(self, worksheet, row, formats, page):
        company_name = ''
        for company in page.company_ids:
            company_name += company.name + ' '
        if page.all_subsidiaries:
            company_name = company_name + ' plus all organisational children'
        if not company_name:
            company_name = self.env.company.name
        worksheet.write(row, 0, company_name, formats.title)
        return row

    def check_consolidate_multi_company(self, group):
        super(AddinFinancialReportDownload, self).check_consolidate_multi_company(group)
        if group.consolidate_multi_company:
            return True
        return False

    def print_lines(self, DATA_COLUMN_START, group, worksheet, row, line, group_format,
                    group_sum, formats, signum, include_account_code):
        """
        overwrite of core so we include the company name in the account name if they print detailed not rolled up
        """

        if group.print_accounts:
            if line.download_id.report_id.chart_id.include_coy_name:
                if include_account_code:
                    worksheet.write(row, 0, line.account_code, group_format.account)
                    worksheet.write(row, 1, line.account_name + ' - ' + line.account_id.company_id.name,
                                    group_format.account)
                else:
                    worksheet.write(row, 0, line.account_name + ' - ' + line.account_id.company_id.name,
                                    group_format.account)
            else:
                if include_account_code:
                    worksheet.write(row, 0, line.account_code, group_format.account)
                    worksheet.write(row, 1, line.account_name, group_format.account)
                else:
                    worksheet.write(row, 0, line.account_name, group_format.account)

        col = DATA_COLUMN_START
        for col_data in line.col_data_ids:
            if group.print_accounts:
                if col_data.column_id.column_type == "variance":

                    v1_cell = xl_rowcol_to_cell(row, col + col_data.v1_offset)
                    v2_cell = xl_rowcol_to_cell(row, col + col_data.v2_offset)
                    formula = "={v1}-{v2}".format(v1=v1_cell, v2=v2_cell)
                    worksheet.write_formula(row, col, formula, formats.default_dollar)

                elif col_data.column_id.column_type == "variance-percent":

                    v1_cell = xl_rowcol_to_cell(row, col + col_data.v1_offset)
                    v2_cell = xl_rowcol_to_cell(row, col + col_data.v2_offset)
                    formula = "=IF(ABS({v1})>0,({v2}-{v1})/{v1},0)".format(v1=v1_cell, v2=v2_cell)
                    worksheet.write_formula(row, col, formula, formats.default_percent)

                else:
                    worksheet.write(row, col, signum * col_data.value, formats.default_dollar)

            group_sum.add(col_data.column_id.id, col_data.value)
            col += 1
        if group.print_accounts:
            row += 1

        return group_sum, row

    def print_consolidate_multi_company_lines(self, DATA_COLUMN_START, group, worksheet, row, lines, group_format,
                                              group_sum, formats, signum):
        group_sum, row = super(AddinFinancialReportDownload, self).print_consolidate_multi_company_lines(
            DATA_COLUMN_START, group, worksheet, row, lines,
            group_format, group_sum, formats, signum)
        accum_values = {}
        account_code = lines[0].account_code
        account_name = lines[0].account_name
        for line in lines:
            if line.account_code == account_code:
                col = DATA_COLUMN_START
                for col_data in line.col_data_ids:
                    if accum_values.get(col, None):
                        accum_values[col] += col_data.value
                    else:
                        accum_values[col] = col_data.value
                    col += 1
                    group_sum.add(col_data.column_id.id, col_data.value)
            else:
                if group.print_accounts:
                    worksheet.write(row, 0, account_code, group_format.account)
                    worksheet.write(row, 1, account_name, group_format.account)
                    col = DATA_COLUMN_START
                    for col_data in line.col_data_ids:
                        if col_data.column_id.column_type == "variance":

                            v1_cell = xl_rowcol_to_cell(row, col + col_data.v1_offset)
                            v2_cell = xl_rowcol_to_cell(row, col + col_data.v2_offset)
                            formula = "={v1}-{v2}".format(v1=v1_cell, v2=v2_cell)
                            worksheet.write_formula(row, col, formula, formats.default_dollar)

                        elif col_data.column_id.column_type == "variance-percent":

                            v1_cell = xl_rowcol_to_cell(row, col + col_data.v1_offset)
                            v2_cell = xl_rowcol_to_cell(row, col + col_data.v2_offset)
                            formula = "=IF(ABS({v1})>0,({v2}-{v1})/{v1},0)".format(v1=v1_cell, v2=v2_cell)
                            worksheet.write_formula(row, col, formula, formats.default_percent)
                        else:
                            worksheet.write(row, col, signum * accum_values[col], formats.default_dollar)
                        col += 1
                    row += 1
                accum_values = {}
                account_code = line.account_code
                account_name = line.account_name
                col = DATA_COLUMN_START
                for col_data in line.col_data_ids:
                    if accum_values.get(col, None):
                        accum_values[col] += col_data.value
                    else:
                        accum_values[col] = col_data.value
                    col += 1
                    group_sum.add(col_data.column_id.id, col_data.value)

        # handle last line if same code as previous line
        if group.print_accounts:
            worksheet.write(row, 0, line.account_code, group_format.account)
            worksheet.write(row, 1, line.account_name, group_format.account)
            col = DATA_COLUMN_START
            for col_data in line.col_data_ids:
                if col_data.column_id.column_type == "variance":

                    v1_cell = xl_rowcol_to_cell(row, col + col_data.v1_offset)
                    v2_cell = xl_rowcol_to_cell(row, col + col_data.v2_offset)
                    formula = "={v1}-{v2}".format(v1=v1_cell, v2=v2_cell)
                    worksheet.write_formula(row, col, formula, formats.default_dollar)

                elif col_data.column_id.column_type == "variance-percent":

                    v1_cell = xl_rowcol_to_cell(row, col + col_data.v1_offset)
                    v2_cell = xl_rowcol_to_cell(row, col + col_data.v2_offset)
                    formula = "=IF(ABS({v1})>0,({v2}-{v1})/{v1},0)".format(v1=v1_cell, v2=v2_cell)
                    worksheet.write_formula(row, col, formula, formats.default_percent)
                else:
                    worksheet.write(row, col, signum * accum_values[col], formats.default_dollar)
                col += 1
            row += 1

        return group_sum, row
