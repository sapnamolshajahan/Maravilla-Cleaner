# -*- coding: utf-8 -*-
import base64
import logging
from io import BytesIO as StringIO

from xlsxwriter import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name

from odoo import api, fields, models
from odoo.addons.queue_job.delay import chain
from .chart_type_builder import ChartTypeBuilder, ProfitLossBuilder, BalanceSheetBuilder
from ..models import financial_report_constants as C
from ..models.addin_styling import AddinStyleFormats

_logger = logging.getLogger(__name__)


class GroupSum():
    """
    Small class to hold Group totals and row counters
    """

    def __init__(self, row):
        self.row = row
        self.totals = {}

    def add(self, col_id, value):
        if col_id in self.totals:
            self.totals[col_id] += value
        else:
            self.totals[col_id] = value
        return self

    def has_stuff(self):
        return len(self.totals) > 0

    def value(self, col_id):
        return self.totals[col_id]

    def merge(self, group_sum):
        self.row = group_sum.row
        for k in group_sum.totals.keys():
            self.add(k, group_sum.value(k))
        return self


class GroupRatio():
    """
    Small class to hold Ratio totals
    """

    def __init__(self):
        self.ratio_totals = {}

    def add(self, group, col_id, value):
        if group in self.ratio_totals:
            if col_id in self.ratio_totals[group]:
                self.ratio_totals[group][col_id] += value
            else:
                self.ratio_totals[group][col_id] = value
        else:
            self.ratio_totals[group] = {}
            self.ratio_totals[group][col_id] = value
        return self

    def value(self, group, col_id):
        try:
            return self.ratio_totals[group][col_id]
        except:
            return 0


class FinancialReportDownload(models.TransientModel):
    _name = "addin.financial.report.download"
    _description = "Financial Report Download"

    ################################################################################
    # Fields
    ################################################################################
    email = fields.Char("Email To", required=True, default=lambda self: self.env.user.partner_id.email)
    user = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    report_name = fields.Char(readonly=True, string="Download Name")
    data = fields.Binary(string="Report Download", readonly=True, attachment=False)
    report_id = fields.Many2one("addin.financial.report", string="Report",
                                readonly=True, ondelete="cascade", required=True)
    report_format = fields.Selection(related="report_id.output",
                                     selection=C.REPORT_OUTPUT_SELECTION, string="Output")
    styling = fields.Many2one("addin.styling", string="Styling to be applied", related="report_id.styling")
    chart_name = fields.Char(related="report_id.chart_id.name", string="Chart Name")

    ################################################################################
    # Business Methods
    ################################################################################
    def create_wizard(self, fin_report):
        """
        :param fin_report: addin.financial.report singleton
        """
        return self.create(
            {
                "report_id": fin_report.id,
            })

    def run_report(self):
        """
        Button: run the report
        """
        chain(
            self.build_data(),
            self.delayable(
                channel=self.light_job_channel(),
                description="Financial Report: Construct xls"
            ).build_xls(),
            self.delayable(
                channel=self.light_job_channel(),
                description=f"Final Report: Email Report"
            ).email_report()
        ).delay()
        return {"type": "ir.actions.act_window_close"}

    def get_chart_builder(self):
        """
        Factory method to get appropriate Report Builder
        """
        if self.report_id.chart_id.type == "balance-sheet":
            return BalanceSheetBuilder(self)
        if self.report_id.chart_id.type in ("profit-loss", "cashflow"):
            return ProfitLossBuilder(self)

        raise Exception(f"Unhandled chart-type={self.report_id.chart_id.type}")

    def build_data(self):
        """
        Return groups of jobs to run
        """
        builder = self.get_chart_builder()
        prep_group = builder.prep_summary_jobs()
        if prep_group:
            return chain(
                prep_group,
                self.delayable(
                    channel=self.light_job_channel(),
                    description="Financial Report: Build Data after Prep"
                )._build_data_as_job())

        return self.delayable(
            channel=self.light_job_channel(),
            description="Financial Report: Build Data"
        )._build_data_as_job()

    def _build_data_as_job(self):
        """
        Run the data-builder; intended to run as a job
        """
        self.get_chart_builder().build_data()

    def email_report(self):
        """
        Mail the report to the user
        """
        body_html = f"<p>Hi,</p><p>Attached is the requested {self.report_id.name}</p>"
        email = self.env["mail.mail"].sudo().create(
            {
                "body_html": body_html,
                "state": "outgoing",
                "author_id": self.user.partner_id.id,
                "email_from": self.user.email_formatted,
                "email_to": self.email,
                "subject": f"{self.report_id.name}",
            })
        attachment = self.env["ir.attachment"].sudo().create(
            {
                "name": self.report_name,
                "datas": self.data,
                "type": "binary",
                "mimetype": "application/octet-stream",
                "description": f"{self.report_id.name}",
                "res_model": email._name,
                "res_id": email.id,
            })
        email.write(
            {
                "attachment_ids": [(4, attachment.id)]
            })
        email.send()
        _logger.debug(f"sent aged-debtor-report to {self.email}")

    def _get_report_name(self):
        """
        Get the download file name.
        """
        return f"{self.report_id.company_id.name}_{self.report_id.name}.{self.report_format}"

    def build_xls(self):
        """
        Present and store report data as Excel spreadsheet.
        """
        data = StringIO()
        workbook = Workbook(data, {"in_memory": True})

        # Generate display formats
        if self.styling:
            formats = self.styling.generate_formats(self.report_id.rounding, workbook)
        else:
            if self.report_id.rounding == "dollars":
                dollar_format = "0"
            else:
                dollar_format = "0.00"
            formats = AddinStyleFormats(dollar_format, workbook)

        # Build spreadsheet pages
        for page in self.report_id.chart_id.page_ids:
            worksheet = workbook.add_worksheet(page.name)
            report_date = fields.Date.context_today(self)
            report_date = str(report_date.day) + '/' + str(report_date.month) + '/' + str(report_date.year)

            report_end_date = self.report_id.date_end
            report_end_date = str(report_end_date.day) + ' ' + str(report_end_date.strftime("%B")) + ' ' + str(
                report_end_date.year)

            row = 0

            if self.report_id.print_company_name:
                worksheet.write(row, 0, self.report_id.company_id.name, formats.title)
                row += 1

            if self.report_id.print_report_name:
                worksheet.write(row, 0, self.report_id.name, formats.chart)
                row += 1

            if self.report_id.print_as_at_date:
                worksheet.write(row, 0, "As At " + report_end_date, formats.chart)

            # Heading for Columns
            row += 1
            if self.report_id.chart_id.include_account_code:
                col = 2
            else:
                col = 1
            for column in self.report_id.column_ids:
                worksheet.write(row, col, column.build_column_name(), formats.column)
                col += 1

            row += 1
            group_ratio = GroupRatio()
            for group in self.report_id.chart_id.account_group_id:
                groupsum, row = self.build_xls_group(worksheet, row, page, group, 0, formats,
                                                     self.report_id.chart_id.include_account_code, group_ratio)

            if self.report_id.print_run_date:
                row += 1
                worksheet.write(row, 0, "Run Date: " + str(report_date), formats.parameters)

            worksheet.set_column('A:A', self.styling.col_width_name)
            worksheet.set_column('B:B', self.styling.col_width_desc)
            final_column = xl_col_to_name(col)
            col_range = 'C:' + final_column
            worksheet.set_column(col_range, self.styling.col_width_value)

        workbook.close()
        data.seek(0)
        output = base64.encodebytes(data.read())
        self.write(
            {
                "report_name": self._get_report_name(),
                "data": output,
            })

    def print_lines(self, DATA_COLUMN_START, group, worksheet, row, line, group_format, group_sum, formats, signum,
                    include_account_code):
        if group.print_accounts:
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

    def check_consolidate_multi_company(self, group):
        return False

    def print_consolidate_multi_company_lines(self, DATA_COLUMN_START, group, worksheet, row, lines, group_format,
                                              group_sum, formats, signum):
        return group_sum, row

    def build_xls_group(self, worksheet, row, page, group, depth, formats, include_account_code, group_ratio):
        """
        lines with a common group.

        Col 0 : account-code
        Col 1 : name
        Col 2+ data

        """
        group_format = formats.delve(depth)

        if include_account_code:
            DATA_COLUMN_START = 2
        else:
            DATA_COLUMN_START = 1
        if group.signage:
            signum = -1
        else:
            signum = 1
        if group.heading:
            row += group.lines_before
            worksheet.write(row, 0, group.name, group_format.header)
            row += 1

        group_sum = GroupSum(row)
        lines = self.env["addin.financial.report.download.line"].search(
            [
                ("download_id", "=", self.id),
                ("page_id", "=", page.id),
                ("group_id", "=", group.id),
            ], order="account_code")

        consolidate_multi_company = self.check_consolidate_multi_company(group)

        if consolidate_multi_company and lines:
            group_sum, row = self.print_consolidate_multi_company_lines(DATA_COLUMN_START, group, worksheet, row, lines,
                                                                        group_format, group_sum, formats, signum)
        else:
            for line in lines:
                group_sum, row = self.print_lines(DATA_COLUMN_START, group, worksheet, row, line, group_format,
                                                  group_sum, formats, signum, include_account_code)

        #
        # Dig into the group if it has kids
        #
        child_groups = self.env["addin.report.account.group"].search(
            [("parent_id", "=", group.id)],
            order="sequence, id")
        for child in child_groups:
            child_sum, row = self.build_xls_group(worksheet, row, page, child, depth + 1, formats, include_account_code,
                                                  group_ratio)
            row = group_sum.merge(child_sum).row

        # if this is a ratio  group we handle here

        if group.ratio:
            col = DATA_COLUMN_START
            if group.footer_name:
                worksheet.write(row, 0, "{}".format(group.footer_name), group_format.footer)
            else:
                worksheet.write(row, 0, "{}".format(group.name), group_format.footer)
            for column in self.report_id.column_ids:
                if column.column_type not in ("variance", "variance-percent"):
                    value_top = group_ratio.value(group.numerator_group.id, col)
                    value_bottom = group_ratio.value(group.denomintor_group.id, col)
                    if value_bottom:
                        ratio = value_top / value_bottom
                    else:
                        ratio = 0.0

                    worksheet.write(row, col, ratio, group_format.footer_percent)
                else:
                    worksheet.write(row, col, "", group_format.footer_percent)

                col += 1

            row += 1
            row += group.lines_after

        # Print group subtotals
        if group.subtotal and group_sum.has_stuff() and not group.ratio:
            col = DATA_COLUMN_START
            if not group.print_accounts:
                if group.footer_name:
                    worksheet.write(row, 0, "{}".format(group.footer_name), group_format.footer)
                else:
                    worksheet.write(row, 0, "{}".format(group.name), group_format.footer)
            else:
                if group.footer_name:
                    worksheet.write(row, 0, "{}".format(group.footer_name), group_format.footer)
                else:
                    worksheet.write(row, 0, "{}".format(group.name), group_format.footer)

            for column in self.report_id.column_ids:
                if column.column_type == "variance":

                    v1_offset, v2_offset = ChartTypeBuilder.build_data_variance_offsets(column)
                    v1_cell = xl_rowcol_to_cell(row, col + v1_offset)
                    v2_cell = xl_rowcol_to_cell(row, col + v2_offset)
                    formula = "={v1}-{v2}".format(v1=v1_cell, v2=v2_cell)
                    worksheet.write_formula(row, col, formula, group_format.footer_cell)

                elif column.column_type == "variance-percent":

                    v1_offset, v2_offset = ChartTypeBuilder.build_data_variance_offsets(column)
                    v1_cell = xl_rowcol_to_cell(row, col + v1_offset)
                    v2_cell = xl_rowcol_to_cell(row, col + v2_offset)
                    formula = "=IF(ABS({v1})>0,({v2}-{v1})/{v1},0)".format(v1=v1_cell, v2=v2_cell)
                    worksheet.write_formula(row, col, formula, group_format.footer_percent)

                else:
                    worksheet.write(row, col, signum * group_sum.value(column.id), group_format.footer_cell)
                    group_ratio.add(group.id, col, group_sum.value(column.id))

                col += 1
            row += 1
            row += group.lines_after

        elif not group.subtotal and group_sum.has_stuff() and not group.ratio:
            col = DATA_COLUMN_START
            for column in self.report_id.column_ids:
                group_ratio.add(group.id, col, group_sum.value(column.id))
                col += 1

        group_sum.row = row
        return group_sum, row


class FinancialReportDownloadLine(models.TransientModel):
    _name = "addin.financial.report.download.line"

    ################################################################################
    # Fields
    ################################################################################
    download_id = fields.Many2one("addin.financial.report.download", string="Report", ondelete="cascade", required=True)
    group_id = fields.Many2one("addin.report.account.group", string="Account Group", required=True, ondelete="cascade")
    group_depth = fields.Integer("Expanded Group depth", required=True, default=0)
    page_id = fields.Many2one("addin.report.chart.page", string="Page Group")
    account_id = fields.Many2one("account.account", string="Account")
    col_data_ids = fields.One2many("addin.financial.report.download.column", "download_line_id", string="Column Data")
    account_code = fields.Char(string="Account Code")
    account_name = fields.Char(string="Account Name")
    company_id = fields.Many2one(comodel_name='res.company', string="Company")


class FinancialReportDownloadColumn(models.TransientModel):
    _name = "addin.financial.report.download.column"

    ################################################################################
    # Fields
    ################################################################################
    download_line_id = fields.Many2one("addin.financial.report.download.line", string="Line", ondelete="cascade",
                                       required=True)
    column_id = fields.Many2one("addin.financial.report.column", string="Column", ondelete="cascade", required=True)
    value = fields.Float(string="Value", required=True, default=0)
    v1_offset = fields.Integer("Variance Col1 offset", default=0, help="Used when column_type = 'variance*'")
    v2_offset = fields.Integer("Variance Col2 offset", default=0, help="Used when column_type = 'variance*'")


class BalanceSheetScratch(models.TransientModel):
    """
    Scratchpad for BalanceSheetBuilder
    """
    _name = "addin.financial.chartbuilder.balance"
    _description = __doc__
    _sql_constraints = [
        ("unique_account_period", "unique(download, account, period)", "Internal Error"),
    ]

    ################################################################################
    # Fields
    ################################################################################
    download = fields.Many2one("addin.financial.report.download", string="Report", ondelete="cascade", required=True)
    account = fields.Many2one("account.account", string="Account", required=True)
    period = fields.Char("Period Name", required=True)
    period_sum = fields.Float("Period Total", required=True, default=0)

    @api.model
    def calc_sum(self, download, account_id, date_from, date_to):
        """
        Calculate the monthly sum for an account.

        Intended to be run as a job.

        :param download: addin.financial.report.download singleton
        :param account_id: account.account id value
        """
        sql = f"""
            insert into {self._table} (download, account, period, period_sum)
            select %(download_id)s, %(account_id)s, to_char (account_move_line.date, 'YYYY-MM'), sum (debit - credit)
            from account_move_line, account_move
            where account_id = %(account_id)s
            and account_move_line.move_id = account_move.id
        """.strip()
        if download.report_id.include_draft:
            sql += " and account_move.state != 'cancel'"
        else:
            sql += " and account_move.state = 'posted'"
        sql += " group by account_id, to_char (account_move_line.date, 'YYYY-MM')"
        self.env.cr.execute(sql,
                            {
                                "account_id": account_id,
                                "download_id": download.id,
                            })

    @api.model
    def calc_retained_sum(self, download, account_id, date_from, date_to):
        """
        Calculate the monthly sum for an retained account, including expenses as well.

        Intended to be run as a job.

        :param download: addin.financial.report.download singleton
        :param account_id: account.account id value
        """
        ret_earn_acc = self.env["account.account"].browse(account_id)

        # Remove cached values for retained+expenses
        sql = f"""
            delete from {self._table}
            using account_account
            where download = %(download_id)s
            and
            (
                account_account.id = %(account_id)s
             or include_initial_balance = false
            )
            and account_account.company_id = %(company_id)s
            and account = account_account.id
        """.strip()
        self.env.cr.execute(sql,
                            {
                                "account_id": account_id,
                                "company_id": ret_earn_acc.company_id.id,
                                "download_id": download.id,
                            })

        # Update scratch for retained earnings + expenses
        sql = f"""
            insert into {self._table} (download, account, period, period_sum)
            select %(download_id)s, %(account_id)s, to_char (account_move_line.date, 'YYYY-MM'), sum (debit - credit)
            from account_account, account_move_line, account_move
            where
            (
                account_account.id = %(account_id)s
             or include_initial_balance = false
            )
            and account_account.company_id = %(company_id)s
            and account_id = account_account.id
            and account_move_line.move_id = account_move.id
        """.strip()
        if download.report_id.include_draft:
            sql += " and account_move.state != 'cancel'"
        else:
            sql += " and account_move.state = 'posted'"
        sql += " group by to_char (account_move_line.date, 'YYYY-MM')"
        self.env.cr.execute(sql,
                            {
                                "account_id": account_id,
                                "company_id": ret_earn_acc.company_id.id,
                                "download_id": download.id,
                            })

    @api.model
    def extract_sum(self, download, account, date):
        """
        Extract summary values from scratch table.
        """
        # include a count(*) so that we always have a period_sum value, even if no rows are found
        sql = f"""
            select coalesce (sum (period_sum), 0), count (*)
            from {self._table}
            where download = %(download_id)s
            and account = %(account_id)s
            and period <= '{date.year}-{date.month:02d}'
        """.strip()
        self.env.cr.execute(sql,
                            {
                                "account_id": account.id,
                                "download_id": download.id,
                            })
        results = self.env.cr.fetchall()
        return results[0][0]
