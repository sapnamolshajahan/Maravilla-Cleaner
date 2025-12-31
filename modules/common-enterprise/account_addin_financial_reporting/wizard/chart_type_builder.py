# -*- coding: utf-8 -*-
import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from odoo.addons.queue_job.delay import chain, group

from odoo import fields

_logger = logging.getLogger(__name__)


class AcidItem:
    """
    Small data holder
    """

    def __init__(self, acid, group_id, depth):
        self.acid = acid
        self.group = group_id
        self.depth = depth


class ChartTypeBuilder(object):
    """
    Abstract class for report builder.
    """

    def __init__(self, download):
        self.download = download
        self.env = download.env

    def get_companies(self):
        """
        Get companies in question.
        Multiple companies may be returned.

        :return: iterable company-ids.
        """
        return [self.download.report_id.company_id.id]

    def acid_items_hook(self, acid_items):
        result = acid_items
        return result

    def early_date(self, report):
        early_date = new_early_date = report.date_end

        for column in report.column_ids:
            if column.column_type in ('actual_period', 'actual_ytd', 'budget_period', 'budget_ytd'):
                if int(column.column_value):
                    new_early_date = report.date_end - relativedelta(months=int(column.column_value))
            elif column.column_type in ('actual_ly', 'budget_year', 'actual_lytd', 'budget_lytd'):
                if int(column.column_value):
                    new_early_date = report.date_end - relativedelta(months=24 + int(column.column_value))
                else:
                    new_early_date = report.date_end - relativedelta(months=24)
            if new_early_date < early_date:
                early_date = new_early_date
        return early_date

    def _distill_acid(self, report):
        company_ids = self.get_companies()
        acid_items = self.expand_account_groups(company_ids, report.chart_id.account_group_id, 0)
        return self.acid_items_hook(acid_items)

    def build_data(self):
        """
        :param download: addin.financial.report.download singleton
        :return: chain of jobs to run
        """
        report = self.download.report_id
        acid_items = self._distill_acid(report)
        budget_set = set()
        for column in report.column_ids:
            if column.budget_id:
                budget_set.add(column.budget_id.id)

        # Work thru' the pages
        for page in report.chart_id.page_ids:

            self.build_download_lines(self.download, page, acid_items, list(budget_set))

            lines = self.env["addin.financial.report.download.line"].search(
                [
                    ("download_id", "=", self.download.id),
                    ("page_id", "=", page.id),
                ])

            _logger.debug("build page={}, line-count={}".format(page.name, len(lines.ids)))
            for column in report.column_ids:
                self.build_column_data(column, lines)

    def expand_account_groups(self, company_ids, group, depth):
        """
        @return list of AcidItem
        """
        acid_set = set()
        if group.account_tag_ids:
            account_ids = self.env["account.account"].sudo().search(
                [
                    ("company_id", "in", company_ids),
                    ("tag_ids", "in", [x.id for x in group.account_tag_ids]),
                ])
            for account in account_ids:
                acid_set.add(account.id)

        for account in group.account_ids:
            acid_set.add(account.id)

        result = []
        for acid in acid_set:
            result.append(AcidItem(acid, group.id, depth))

        #
        # Dig into the group if it has kids
        #
        child_groups = self.env["addin.report.account.group"].search(
            [("parent_id", "=", group.id)],
            order="sequence, id")
        for child in child_groups:
            result.extend(self.expand_account_groups(company_ids, child, depth + 1))

        return result

    def prep_summary_jobs(self):
        """
        Prepare a group of jobs to run before the actual data-gather

        :return: group of jobs to run or None
        """
        _logger.debug("prep_summary_data - do nothing")
        return None

    def multi_company_hook(self, acid_items, page):
        return acid_items

    def do_consolidate_multi_company(self, recs):
        return

    def check_consolidate_multi_company(self):
        return False

    def build_download_lines(self, download, page, acid_items, budget_ids):
        """
        :param download: "addin.financial.report.download" singleton
        :param page: "addin.report.chart.page" singleton
        :param budget_ids: list of budget-ids
        """

        account_model = self.env["account.account"].sudo()
        acid_items = self.multi_company_hook(acid_items, page)

        groups = []
        acid_lookup = {}
        for item in acid_items:
            key = str(item.acid) + '-' + str(item.group)
            acid_lookup[key] = item
            groups.append(item.group)

        set_groups = list(set(groups))

        chart = page.chart_id

        for rec in acid_items:
            account = account_model.browse(rec.acid)
            p_code = account.code
            p_name = account.name

            if code:
                code += "." + p_code
            else:
                code = p_code
            if account_name:
                account_name += " - " + p_name
            else:
                account_name = p_name

            for i in range(0, len(set_groups)):
                group = set_groups[i]
                key = str(account.id) + '-' + str(group)
                if acid_lookup.get(key, False):
                    self.env['addin.financial.report.download.line'].create(
                        {
                            "download_id": download.id,
                            "group_id": acid_lookup[key].group,
                            "group_depth": acid_lookup[key].depth,
                            "account_code": code,
                            "page_id": page.id,
                            "account_id": account.id,
                            "account_name": account_name,
                            "company_id": account.company_id.id,
                        })

    def build_column_data(self, column, lines):
        """
        Stub
        """
        raise Exception("Internal Error")

    def get_last_fiscalyear_end(self, closing_date):
        fiscal_last_month = int(self.env.company.fiscalyear_last_month)
        fiscal_last_day = int(self.env.company.fiscalyear_last_day)
        if closing_date.month <= fiscal_last_month:
            last_fiscal_year_end_str = '{year}-{month}-{day}'.format(year=closing_date.year - 1,
                                                                     month=fiscal_last_month, day=fiscal_last_day)
        else:
            last_fiscal_year_end_str = '{year}-{month}-{day}'.format(year=closing_date.year, month=fiscal_last_month,
                                                                     day=fiscal_last_day)
        last_fiscal_year_end = fields.Date.from_string(last_fiscal_year_end_str)
        return last_fiscal_year_end

    def build_data_dates_period(self, column):
        """
        Dates for a columns' period

        Work out the start date; moving from the 1st day of the month
        to avoid varying month ends
        """
        end_date = column.date_end
        first_date = end_date.replace(day=1)
        back_date = first_date + relativedelta(months=-column.period_count + 1)  # ie if months=1 do nothing

        return (back_date, column.date_end)

    def build_data_dates_ytd(self, column):
        """
        Financial YTD date range

               FIN                    COL
               END                    END
                |                      |
        --------v----------------------v------------------
                 ***********************

        """
        # Work out the start date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)
        end_date = fields.Date.from_string(column.date_end)
        if end_date.month > int(last_fin_month):
            date_start = date(year=end_date.year, month=int(last_fin_month) + 1, day=1)
        else:
            if int(last_fin_month) == 12:
                date_start = date(year=end_date.year, month=1, day=1)
            else:
                date_start = date(year=end_date.year - 1, month=int(last_fin_month) + 1, day=1)

        return (date_start, column.date_end)

    def build_data_dates_lytd(self, column):
        """
        Actual LYTD date range

               FIN        COL        FIN        COL
             END-1yr    END-1yr      END        END
                |          |          |          |
        --------v----------v----------v----------v--------
                 ***********
        """
        # Work out the last financial year-end date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)
        end_date = column.date_end
        if end_date.month == 2 and end_date.day == 29:
            day = 28
        else:
            day = end_date.day
        date_end = date(year=end_date.year - 1, month=end_date.month, day=day)
        if end_date.month > int(last_fin_month):
            date_start = date(year=end_date.year - 1, month=int(last_fin_month) + 1, day=1)
        else:
            if int(last_fin_month) == 12:
                date_start = date(year=end_date.year - 1, month=1, day=1)
            else:
                date_start = date(year=end_date.year - 2, month=int(last_fin_month) + 1, day=1)

        return (date_start, date_end)

    def build_data_dates_ly(self, column):
        """
        Last Financial Year

               FIN        COL        FIN        COL
             END-1yr    END-1yr      END        END
                |          |          |          |
        --------v----------v----------v----------v--------
                 **********************
        """
        # Work out the last financial year-end date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)

        end_date = column.date_end
        if end_date.month > last_fin_month:
            fin_year_end = date(end_date.year, int(last_fin_month), 1) + relativedelta(months=1, days=-1)
            fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
        else:
            if int(last_fin_month) == 12:
                fin_year_end = date(end_date.year, int(last_fin_month), 1) + relativedelta(months=1, days=-1)
                fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
            else:
                fin_year_end = date(end_date.year - 1, int(last_fin_month), 1) + relativedelta(months=1, days=-1)
                fin_year_start = fin_year_end + relativedelta(months=-12, days=1)

        return (fin_year_start, fin_year_end)

    def build_data_dates_year(self, column):
        """
        Current Financial Year for Budgets

               FIN        COL        FIN
               END        END      END+1yr
                |          |          |
        --------v----------v----------v
                 **********************
        """
        # Work out the last financial year-end date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)
        end_date = column.date_end
        if end_date.month > last_fin_month:
            fin_year_end = date(end_date.year + 1, last_fin_month, 1) + relativedelta(months=1, days=-1)
            fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
        else:
            fin_year_end = date(end_date.year, last_fin_month, 1) + relativedelta(months=1, days=-1)
            fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
        return (fin_year_start, fin_year_end)

    def sum_budgets_attributes(self, domain, line):
        return domain

    def sum_budgets(self, column, line, date_start, date_end):
        """
        Create column values with sum of account.financial.budget.line within a date range.
        """
        domain = []
        if date_start and date_end:
            domain = [
                ("date", ">=", date_start),
                ("date", "<=", date_end),
                ("budget_id", "=", column.budget_id.id),
            ]
        elif date_start:
            domain = [
                ("date", ">=", date_start),
                ("budget_id", "=", column.budget_id.id),
            ]
        elif date_end:
            domain = [
                ("date", "<=", date_end),
                ("budget_id", "=", column.budget_id.id),
            ]

        for field in "account_id":
            if line["account_id"]:
                domain.append((field, "=", line["account_id"].id))

        domain = self.sum_budgets_attributes(domain, line)

        budget_lines = self.env["account.report.budget.item"].search(domain)

        rate = 1
        if line['account_id']:
            company = line['account_id'].company_id
            if company.currency_id.id != self.env.company.currency_id.id:
                report_date = column.report_id.date_end
                rate = self.env['res.currency']._get_conversion_rate(company.currency_id, self.env.company.currency_id,
                                                                     self.env.company, report_date)

        if budget_lines:
            value = sum([x.amount * rate for x in budget_lines])
        else:
            value = 0
        self.env["addin.financial.report.download.column"].create(
            {
                "download_line_id": line.id,
                "column_id": column.id,
                "value": value,
            })

    def build_data_variance(self, column, line, v1_offset, v2_offset):
        """
        The variance columns values do not need to be computed.
        The Excel output will use formulas to present the values.
        """
        self.env["addin.financial.report.download.column"].create(
            {
                "download_line_id": line.id,
                "column_id": column.id,
                "v1_offset": v1_offset,
                "v2_offset": v2_offset,
            })

    @staticmethod
    def build_data_variance_offsets(column):
        """
        Build the offsets for variance column references.

        @param column addin.financial.report.column
        @return (offset1, offset2) tuple
        """
        columns = column.report_id.column_ids.sorted(key=lambda r: r.sequence)

        vcol_index = -1
        for i, c in enumerate(columns):
            if c.id == column.id:
                vcol_index = i
                break

        v1_offset = v2_offset = 0
        for i, c in enumerate(columns):
            if c.sequence == column.variance_1_seq:
                v1_offset = i - vcol_index
                break
        for i, c in enumerate(columns):
            if c.sequence == column.variance_2_seq:
                v2_offset = i - vcol_index
                break

        return (v1_offset, v2_offset)


class ProfitLossBuilder(ChartTypeBuilder):

    def opening_balance_start_end_dates(self, column, include_initial_balance):
        """
        include_initial_balance from line account - False for I&E ietms, TRue for Balance Sheet
        """

        date_start = date_end = None
        if column.column_type in ("actual_period", "budget_period"):
            date_start, date_end = self.build_data_dates_period_opening(column, include_initial_balance)
        elif column.column_type in ("actual_ytd", "budget_ytd"):
            date_start, date_end = self.build_data_dates_ytd_opening(column, include_initial_balance)
        elif column.column_type in ("actual_lytd", "budget_lytd"):
            date_start, date_end = self.build_data_dates_lytd_opening(column, include_initial_balance)
        elif column.column_type == "actual_ly":
            date_start, date_end = self.build_data_dates_ly_opening(column, include_initial_balance)
        elif column.column_type == "budget_year":
            date_start, date_end = self.build_data_dates_year_opening(column, include_initial_balance)
        return date_start, date_end

    def build_data_dates_period_opening(self, column, include_initial_balance):
        """
        Dates for a columns' period if opening balance type = True then balance sheet so start date is from day 0

        """
        end_date = column.date_end
        first_date = end_date.replace(day=1)
        back_date = first_date + relativedelta(months=-column.period_count + 1)  # ie if months=1 do nothing
        closing_date = back_date - relativedelta(days=1)

        if not include_initial_balance:
            start_date = self.get_last_fiscalyear_end(closing_date) + relativedelta(days=1)
        else:
            start_date = False

        return (start_date, closing_date)

    def build_data_dates_ytd_opening(self, column, include_initial_balance):
        """
        Financial YTD date range

               FIN                    COL
               END                    END
                |                      |
        --------v----------------------v------------------
                 ***********************

        """
        # Work out the start date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)
        end_date = fields.Date.from_string(column.date_end)
        if end_date.month > last_fin_month:
            date_start = date(end_date.year, last_fin_month + 1, 1)
        else:
            date_start = date(year=end_date.year - 1, month=last_fin_month + 1, day=1)

        if not include_initial_balance:  # expense
            date_start = end_date + relativedelta(days=1)  # ie return 0
        else:
            date_start = False
            end_date = self.get_last_fiscalyear_end(end_date)  # ie the balance as at the end of the last fiscal year

        return (date_start, end_date)

    def build_data_dates_lytd_opening(self, column, include_initial_balance):
        """
        Actual LYTD date range

               FIN        COL        FIN        COL
             END-1yr    END-1yr      END        END
                |          |          |          |
        --------v----------v----------v----------v--------
                 ***********
        """
        # Work out the last financial year-end date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)
        end_date = column.date_end
        if end_date.month == 2 and end_date.day == 29:
            day = 28
        else:
            day = end_date.day
        date_end = date(year=end_date.year - 1, month=end_date.month, day=day)
        if end_date.month > int(last_fin_month):
            date_start = date(year=end_date.year - 1, month=int(last_fin_month) + 1, day=1)
        else:
            if int(last_fin_month) == 12:
                date_start = date(year=end_date.year - 1, month=1, day=1)
            else:
                date_start = date(year=end_date.year - 2, month=int(last_fin_month + 1), day=1)

        if not include_initial_balance:  # expense
            date_start = end_date + relativedelta(days=1)  # ie return 0
        else:
            date_start = False
            date_end = self.get_last_fiscalyear_end(date_end)  # ie the balance as at the end of the last fiscal year -1

        return (date_start, date_end)

    def build_data_dates_ly_opening(self, column, include_initial_balance):
        """
        Last Financial Year

               FIN        COL        FIN        COL
             END-1yr    END-1yr      END        END
                |          |          |          |
        --------v----------v----------v----------v--------
                 **********************
        """
        # Work out the last financial year-end date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)

        end_date = column.date_end
        if end_date.month > int(last_fin_month):
            fin_year_end = date(end_date.year, last_fin_month, 1) + relativedelta(months=1, days=-1)
            fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
        else:
            if int(last_fin_month) == 12:
                fin_year_end = date(end_date.year, 1, 1) + relativedelta(months=1, days=-1)
                fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
            else:
                fin_year_end = date(end_date.year - 1, last_fin_month, 1) + relativedelta(months=1, days=-1)
                fin_year_start = fin_year_end + relativedelta(months=-12, days=1)

        if not include_initial_balance:  # expense
            fin_year_start = fin_year_end + relativedelta(days=1)  # ie return 0
        else:
            fin_year_end = fin_year_start - relativedelta(days=1)  # ie the day before the year starts for other rows
            fin_year_start = False

        start = fin_year_start
        end = fin_year_end

        return (start, end)

    def build_data_dates_year_opening(self, column, include_initial_balance):
        """
        Current Financial Year for Budgets

               FIN        COL        FIN
               END        END      END+1yr
                |          |          |
        --------v----------v----------v
                 **********************
        """
        # Work out the current financial year-end date.
        last_fin_month = int(column.report_id.company_id.fiscalyear_last_month)
        end_date = column.date_end
        if end_date.month > int(last_fin_month):
            fin_year_end = date(end_date.year + 1, int(last_fin_month), 1) + relativedelta(months=1, days=-1)
            fin_year_start = fin_year_end + relativedelta(months=-12, days=1)
        else:
            fin_year_end = date(end_date.year, int(last_fin_month), 1) + relativedelta(months=1, days=-1)
            fin_year_start = fin_year_end + relativedelta(months=-12, days=1)

        if not include_initial_balance:  # expense
            fin_year_start = fin_year_end + relativedelta(days=1)  # ie return 0
        else:
            fin_year_end = fin_year_start - relativedelta(days=1)  # ie the day before the year starts for other rows
            fin_year_start = False

        start = fin_year_start
        end = fin_year_end

        return (start, end)

    def build_column_data(self, column, lines):
        """
        Populate the column data for the configured lines.
        """
        #
        # Determine constraints for the various column-types
        #
        v1_off = v2_off = 0
        if column.column_type.startswith("variance"):
            v1_off, v2_off = self.build_data_variance_offsets(column)

        date_start = date_end = None
        if column.column_type in ("actual_period", "budget_period"):
            date_start, date_end = self.build_data_dates_period(column)
        elif column.column_type in ("actual_ytd", "budget_ytd"):
            date_start, date_end = self.build_data_dates_ytd(column)
        elif column.column_type in ("actual_lytd", "budget_lytd"):
            date_start, date_end = self.build_data_dates_lytd(column)
        elif column.column_type == "actual_ly":
            date_start, date_end = self.build_data_dates_ly(column)
        elif column.column_type == "budget_year":
            date_start, date_end = self.build_data_dates_year(column)

        #
        # Work thru' the lines
        #
        for line in lines:
            if line.group_id.opening_balance and not column.column_type.startswith("variance"):
                opening_date_start, opening_date_end = self.opening_balance_start_end_dates(column,
                                                                                            line.account_id.include_initial_balance)

            if line.group_id.opening_balance and not column.column_type.startswith("variance"):
                use_date_start = opening_date_start
                use_date_end = opening_date_end
            else:
                use_date_start = date_start
                use_date_end = date_end

            if column.column_type.startswith("actual"):
                self.sum_move_lines(column, line, use_date_start, use_date_end)
            elif column.column_type.startswith("budget"):
                self.sum_budgets(column, line, use_date_start, use_date_end)
            elif column.column_type.startswith("variance"):
                self.build_data_variance(column, line, v1_off, v2_off)

    def sum_move_lines_constraint(self, column):
        constraint = sql_and(None, "account_move_line.company_id = {}".format(column.report_id.company_id.id))
        return constraint

    def sum_move_lines_add_attributes(self, line, constraint, column):
        for field in "account_id":
            if line[field]:
                constraint = sql_and(constraint, f"account_move_line.{field} = {line[field].id}")

            rate = 1
            if line['account_id']:
                company = line['account_id'].company_id
                if company.currency_id.id != self.env.company.currency_id.id:
                    report_date = column.report_id.date_end
                    rate = self.env['res.currency']._get_conversion_rate(company.currency_id,
                                                                         self.env.company.currency_id, self.env.company,
                                                                         report_date)
        return constraint, rate

    def sum_move_lines(self, column, line, date_start, date_end):
        """
        Create column values with sum of account.move.lines within a date range.

        :param column:
        :param line: addin.financial.report.download.line singleton
        """
        tables = "account_move, account_move_line"
        constraint = self.sum_move_lines_constraint(column)
        constraint = sql_and(constraint, "account_move.id = account_move_line.move_id")

        if line.download_id.report_id.include_draft:
            constraint = sql_and(constraint, "account_move.state != 'cancel'")
        else:
            constraint = sql_and(constraint, "account_move.state = 'posted'")

        if date_start and date_end:
            constraint = sql_and(constraint, f"account_move_line.date between '{date_start}' and '{date_end}'")
        elif date_start:
            constraint = sql_and(constraint, f"account_move_line.date >= '{date_start}'")
        elif date_end:
            constraint = sql_and(constraint, f"account_move_line.date <= '{date_end}'")

        constraint, rate = self.sum_move_lines_add_attributes(line, constraint, column)

        if line.page_id.chart_id.type == 'cashflow':
            liquidity_journals = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))])
            constraint = sql_and(constraint,
                                 "account_move.journal_id in ({})".format(
                                     ", ".join([str(x.id) for x in liquidity_journals])))

        if line.page_id.analytic_account:
            # filter for lines that match the analytic account
            # Odoo uses jsonb field 'analytic_distribution' to store analytic information
            constraint = sql_and(constraint,
                                 f"account_move_line.analytic_distribution ?| '{set(line.page_id.analytic_account.ids)}'")

        if line.group_id.debit_only:
            constraint = sql_and(constraint, "debit > 0")
        if line.group_id.credit_only:
            constraint = sql_and(constraint, "credit > 0")

        value = 0
        sql = f"select sum (debit - credit) from {tables} {constraint}"
        _logger.debug(f"sum move-lines sql={sql}")
        self.env.cr.execute(sql)
        for row in self.env.cr.fetchall():
            if row[0]:
                value = row[0] * rate
            break

        self.env["addin.financial.report.download.column"].create(
            {
                "download_line_id": line.id,
                "column_id": column.id,
                "value": value,
            })
        _logger.debug('Ending sum_move_lines')

    def sum_budgets_add_attributes(self, line, domain):
        return domain

    def sum_budgets(self, column, line, date_start, date_end):
        domain = []
        if date_start and date_end:
            domain = [
                ("date", ">=", date_start),
                ("date", "<=", date_end),
                ("budget_id", "=", column.budget_id.id),
            ]
        elif date_start:
            domain = [
                ("date", ">=", date_start),
                ("budget_id", "=", column.budget_id.id),
            ]
        elif date_end:
            domain = [
                ("date", "<=", date_end),
                ("budget_id", "=", column.budget_id.id),
            ]
        for field in "account_id":
            if line[field]:
                domain.append((field, "=", line[field].id))

        domain = self.sum_budgets_add_attributes(line, domain)



        if line.page_id.analytic_account:
            domain.append(('analytic_account', 'in', line.page_id.analytic_account.ids))

        budget_lines = self.env["account.report.budget.item"].search(domain)

        rate = 1
        if line['account_id']:
            company = line['account_id'].company_id
            if company.currency_id.id != self.env.company.currency_id.id:
                report_date = column.report_id.date_end
                rate = self.env['res.currency']._get_conversion_rate(company.currency_id, self.env.company.currency_id,
                                                                     self.env.company, report_date)

        if budget_lines:
            value = sum([x.amount * rate for x in budget_lines])
        else:
            value = 0
        self.env["addin.financial.report.download.column"].create(
            {
                "download_line_id": line.id,
                "column_id": column.id,
                "value": value,
            })


class BalanceSheetBuilder(ChartTypeBuilder):

    def prep_summary_jobs(self):
        """
        Override to build a cache table for account-summaries.

        :param download: addin.financial.report.download singleton
        :return: group of jobs to run
        """
        report = self.download.report_id

        acid_items = self._distill_acid(report)
        early_date = self.early_date(report)
        latest_date = report.date_end

        calc_jobs = []
        count_max = len(acid_items)
        count = 0
        for item in acid_items:
            count += 1
            calc_jobs.append(
                self.env["addin.financial.chartbuilder.balance"].delayable(
                    channel=self.download.light_job_channel(),
                    description=f"account={item.acid}, {count}/{count_max}"
                ).calc_sum(self.download, item.acid, early_date, latest_date)
            )

        ret_calc_jobs = []
        retained_accounts = self.env["account.account"].search(
            [
                ("account_type", "=", "equity_unaffected"),
                ("company_id", "in", self.get_companies()),
            ])
        for company in self.get_companies():
            coy_retained_accounts = retained_accounts.filtered(lambda x: x.company_id.id == company)
            if len(coy_retained_accounts) > 1:
                raise Exception('Can only have 1 retained earning account')
            if not coy_retained_accounts:
                raise Exception('Must have a retained earning account')
        count_max = len(retained_accounts)
        count = 0
        for account in retained_accounts:
            count += 1
            ret_calc_jobs.append(
                self.env["addin.financial.chartbuilder.balance"].delayable(
                    channel=self.download.light_job_channel(),
                    description=f"retained account={account.id}, {count}/{count_max}"
                ).calc_retained_sum(self.download, account.id, early_date, latest_date)
            )

        return chain(group(*calc_jobs), group(*ret_calc_jobs))

    def build_column_data(self, column, lines):
        """
        Balance sheet only looks at date_end
        """
        #
        # Determine constraints for the various column-types
        #
        v1_off = v2_off = 0
        if column.column_type.startswith("variance"):
            v1_off, v2_off = self.build_data_variance_offsets(column)

        date_start = None
        date_end = None
        if column.column_type in ("actual_period", "budget_period"):
            date_start, date_end = self.build_data_dates_period(column)
        elif column.column_type in ("actual_ytd", "budget_ytd"):
            date_start, date_end = self.build_data_dates_ytd(column)
        elif column.column_type in ("actual_lytd", "budget_lytd"):
            date_start, date_end = self.build_data_dates_lytd(column)
        elif column.column_type == "actual_ly":
            date_start, date_end = self.build_data_dates_ly(column)
        elif column.column_type == "budget_year":
            date_start, date_end = self.build_data_dates_year(column)

        #
        # Work thru' the lines
        #
        for line in lines:
            if column.column_type.startswith("actual"):
                self.extract_summary(column, line, date_end)
            elif column.column_type.startswith("budget"):
                self.sum_budgets(column, line, date_start, date_end)
            elif column.column_type.startswith("variance"):
                self.build_data_variance(column, line, v1_off, v2_off)

    def extract_summary(self, column, line, date_end):

        # used for consolidation across companies with different base currencies
        rate = 1
        company = line.account_id.company_id
        if company.currency_id.id != self.env.company.currency_id.id:
            report_date = column.report_id.date_end
            rate = self.env['res.currency']._get_conversion_rate(company.currency_id, self.env.company.currency_id,
                                                                 self.env.company, report_date)

        amount = self.env["addin.financial.chartbuilder.balance"].extract_sum(self.download, line.account_id, date_end)
        self.env["addin.financial.report.download.column"].create(
            [{
                "download_line_id": line.id,
                "column_id": column.id,
                "value": amount * rate,
            }])


def sql_and(original, condition):
    if original:
        original += "and "
    else:
        original = "where "
    return original + condition + " "
