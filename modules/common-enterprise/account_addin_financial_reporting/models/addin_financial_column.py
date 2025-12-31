# -*- coding: utf-8 -*-
import calendar

from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

from odoo import fields, models, api
from . import financial_report_constants as C


class AddinFinancialReportColumn(models.Model):
    """
    Financial Report Column

    Allows the user to specify columns to show on the report
    """
    _name = "addin.financial.report.column"

    @api.depends("variance_1_seq")
    def _variance_1(self):

        for col in self:
            if col.column_type.startswith("variance"):
                for other in col.report_id.column_ids:
                    if other.column_type.startswith("variance"):
                        continue
                    if other.sequence == col.variance_1_seq:
                        col.variance_1 = other
                        return
            col.variance_1 = None

    @api.depends("variance_2_seq")
    def _variance_2(self):

        for col in self:
            if col.column_type.startswith("variance"):
                for other in col.report_id.column_ids:
                    if other.column_type.startswith("variance"):
                        continue
                    if other.sequence == col.variance_2_seq:
                        col.variance_2 = other
                        return
            col.variance_2 = None

    # Fields
    report_id = fields.Many2one("addin.financial.report", string="Report Name/Title", readonly=True,
                                required=True, index=True, ondelete="cascade")
    sequence = fields.Integer("Sequence", required=True, default=10)
    column_type = fields.Selection(
        C.REPORT_COLUMN_TYPES, default=C.REPORT_COLUMN_TYPES[0][0],
        string="Column Type", required=True)
    column_value = fields.Selection(
        C.REPORT_COLUMN_VALUES, default=C.REPORT_COLUMN_VALUES[0][0],
        string="Column Value", required=True,
        help="The Column value is used to calculate the period range. Period 0 means the report range end period")
    date_end = fields.Date(string="End Date (inclusive)", compute="_date_end", readonly=True)
    budget_id = fields.Many2one("account.report.budget", string="Budget")
    period_count = fields.Integer("No of Periods", default=1, required=True,
                                  help=("The number of periods to include for range columns. "
                                        "If you want a column that is 3 periods up to the "
                                        "range column, set this to 3"))
    variance_1_seq = fields.Integer("Variance Col 1 (Seq)",
                                    help=("The variance calculation subtrahend.  If the variance is "
                                          "this year vs last year and this year is column 1 and last year is column 2, "
                                          "this should be the column 1"))
    variance_1 = fields.Many2one("addin.financial.report.column", string="Variance Column 1", compute="_variance_1")
    variance_2_seq = fields.Integer("Variance Col 2 (Seq)",
                                    help=("The variance calculation minuend.  If the variance is "
                                          "this year vs last year and this year is column 1 and last year is column 2, "
                                          "this should be the column 2"))
    variance_2 = fields.Many2one("addin.financial.report.column", string="Variance Column 2", compute="_variance_2")

    _order = 'report_id, sequence, id'

    @api.constrains("column_type", "budget_id", "variance_1_seq", "variance_2_seq")
    def _validate_column_type(self):
        """
        Validate column-type field requirements.
        """
        for record in self:
            if record.column_type.startswith("budget") and not record.budget_id:
                raise ValidationError("Budget column types require budget references")

            if record.column_type.startswith("variance") and (not record.variance_1 or not record.variance_2):
                raise ValidationError("Variance column type require valid variance sequence references")

    @api.onchange("column_type")
    def onchange_column_type(self):

        if self.column_type.startswith("actual"):
            self.variance_1_seq = None
            self.variance_2_seq = None
            self.variance_1 = None
            self.variance_2 = None
            self.budget_id = False

        elif self.column_type.startswith("budget"):
            self.variance_1_seq = None
            self.variance_2_seq = None
            self.variance_1 = None
            self.variance_2 = None

        elif self.column_type.startswith("variance"):
            self.budget_id = False

    def _date_end(self):

        for col in self:
            offset = int(col.column_value)  # expect a -ve integer
            if offset:
                report_date = fields.Date.from_string(col.report_id.date_end)
                report_first = report_date.replace(day=1)
                back_date = report_first + relativedelta(months=offset)
                _first_day, last_day = calendar.monthrange(back_date.year, back_date.month)
                if report_date.day < last_day:
                    last_day = report_date.day
                col.date_end = fields.Date.to_string(back_date.replace(day=last_day))
            else:
                col.date_end = col.report_id.date_end

    def build_column_name(self):
        """
        function that get calls the returns the print name for the column
        """
        if self.column_type in ("actual_period", "budget_period"):
            col_str = ""
            date_end = self.date_end
            month = date_end.strftime("%b")
            if self.period_count > 1:
                date_end_str = str(self.period_count) + ' Mths to ' + str(month) + '-' + str(date_end.year)
            else:
                date_end_str = str(month) + '-' + str(date_end.year)

            base = C.REPORT_COLUMN_TYPES_DICT[self.column_type]
            if base.find('Period'):
                base_str = base[0:6]
                col_str = "{} {}".format(base_str, date_end_str)
            elif base.find('Actual'):
                if base.find('YTD'):
                    col_str = 'Actual YTD'
                elif base.find('LYTD'):
                    col_str = 'Actual LYTD'
                elif base.find('Last Full Year'):
                    col_str = 'Actual Last Year'
            elif base.find('Budget'):
                if base.find('YTD'):
                    col_str = 'Budget YTD'
                elif base.find('LYTD'):
                    col_str = 'Budget LYTD'
                elif base.find('Last Full Year'):
                    col_str = 'Budget Last Year'

            return col_str

        return C.REPORT_COLUMN_TYPES_DICT[self.column_type]
