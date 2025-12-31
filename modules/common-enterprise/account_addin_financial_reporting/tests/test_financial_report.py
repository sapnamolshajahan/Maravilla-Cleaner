from dateutil.relativedelta import relativedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date
import calendar
from odoo.odoo.tests import tagged


@tagged('account_addin_financial_reporting')
class TestFinancialReports(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Report = self.env['addin.financial.report']
        self.Chart = self.env['addin.report.chart']
        self.Company = self.env['res.company']
        self.Styling = self.env['addin.styling']
        self.account_group = self.env['addin.report.account.group'].search([], limit=1)
        if not self.account_group:
            self.account_group = self.env['addin.report.account.group'].create({
                'name': 'Test Group',
            })
        self.chart = self.Chart.create({
            'name': 'Test Chart',
            'account_group_id': self.account_group.id,
            'type': 'cashflow',
        })
        self.company = self.Company.search([], limit=1) or self.Company.create({
            'name': 'Test Company',
        })

        self.report = self.Report.create({
            'name': 'Test Report',
            'chart_id': self.chart.id,
            'company_id': self.company.id,
            # 'output': 'pdf',
            'range_period_column_value': '0',
            'rounding': 'dollars',
        })

    def test_default_get(self):
        """ Test default_get method to check default values for fields """
        report = self.Report.default_get([])
        self.assertEqual(report['range_period_column_value'], '0', "Range period should default to '0'")
        self.assertEqual(report['rounding'], 'dollars', "Rounding should default to 'dollars'")

    def test_date_end_computation_with_manual_end(self):
        """ Test if date_end is set correctly when manual_end is provided """
        manual_end_date = date(2024, 12, 31)
        self.report.manual_end = manual_end_date
        self.report._date_end()
        self.assertEqual(self.report.date_end, manual_end_date, "Date end should be set to manual_end if provided")

    def test_date_end_computation_without_manual_end(self):
        """ Test if date_end is computed correctly when manual_end is not provided """
        self.report.manual_end = False
        self.report.range_period_column_value = '1'  # End range 1 period back
        self.report._date_end()

        # Calculate expected date_end
        from datetime import datetime
        expected_date = datetime.today().replace(day=1) - relativedelta(months=1)
        _, last_day = calendar.monthrange(expected_date.year, expected_date.month)
        expected_date = expected_date.replace(day=last_day)

        self.assertEqual(self.report.date_end.strftime('%Y-%m-%d'), expected_date.strftime('%Y-%m-%d'),
                         f"Expected date_end to be {expected_date.strftime('%Y-%m-%d')}, but got {self.report.date_end}")

    def test_get_analytic_filter(self):
        """ Test if has_analytic_filter is correctly set based on chart_id """
        self.report.chart_id.has_analytic_filter = True
        self.report._get_analytic_filter()
        self.assertTrue(self.report.has_analytic_filter, "Has analytic filter should be True when chart_id has it")

        self.report.chart_id.has_analytic_filter = False
        self.report._get_analytic_filter()
        self.assertFalse(self.report.has_analytic_filter, "Has analytic filter should be False when chart_id doesn't have it")

    def test_run_report(self):
        """ Test the run_report method to check if it creates a wizard correctly """
        action = self.report.run_report()
        self.assertEqual(action['type'], 'ir.actions.act_window', "Expected action type to be 'ir.actions.act_window'")
        self.assertEqual(action['view_mode'], 'form', "Expected view_mode to be 'form'")
        self.assertTrue(action['res_model'], "Expected res_model to be set for the wizard")
        self.assertTrue(action['res_id'], "Expected res_id to be set for the wizard")
