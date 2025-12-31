from datetime import date

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.odoo.tests import tagged


@tagged('account_addin_financial_reporting')
class TestFinancialReportColumn(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Report = self.env['addin.financial.report']
        self.Column = self.env['addin.financial.report.column']
        self.Chart = self.env['addin.report.chart']
        self.AccountGroup = self.env['addin.report.account.group']  # ✅ Correct model
        self.budget = self.env['account.report.budget'].create({
            'name': 'Test Budget',
        })
        self.account_group = self.AccountGroup.search([], limit=1)
        if not self.account_group:
            self.account_group = self.AccountGroup.create({
                'name': 'Test Group',
            })

        # Create a valid chart
        self.chart = self.Chart.create({
            'name': 'Test Chart',
            'account_group_id': self.account_group.id,
            'type': 'cashflow',
        })

        self.report = self.Report.create({
            'name': 'Test Report',
            'date_end': '2024-12-31',
            'chart_id': self.chart.id,
        })

    def test_variance_computation(self):
        """Test variance computation between columns."""
        Column = self.env['addin.financial.report.column']
        field = Column._fields['column_type']
        selection = list(field.selection)  # make a mutable copy

        if ('variance_period', 'Variance Period') not in selection:
            selection.append(('variance_period', 'Variance Period'))
            field.selection = selection
            field._description_selection = selection

        col1 = Column.create({
            'report_id': self.report.id,
            'sequence': 1,
            'column_type': 'actual_period',
            'column_value': '0',
            'period_count': 1,
        })

        col2 = Column.create({
            'report_id': self.report.id,
            'sequence': 2,
            'column_type': 'actual_period',
            'column_value': '0',
            'period_count': 1,
            'budget_id': self.budget.id,
        })

        variance = Column.create({
            'report_id': self.report.id,
            'sequence': 3,
            'column_type': 'actual_period',
            'variance_1_seq': 1,
            'budget_id': self.budget.id,
            'variance_2_seq': 2,
            'column_value': '0',
            'period_count': 1,
        })

        variance._variance_1()
        variance._variance_2()

        self.assertNotEqual(variance.variance_1, col1, "Variance 1 should not be equal to col1")
        self.assertNotEqual(variance.variance_2, col2, "Variance 2 should not be equal to col2")

    def test_validate_budget_column_requires_budget_id(self):
        """Test that budget column requires budget_id."""
        with self.assertRaises(ValidationError):
            self.env['addin.financial.report.column'].create({
                'report_id': self.report.id,
                'sequence': 10,
                'column_type': 'budget_period',
                'column_value': '0',
                'period_count': 1,
            })

    def test_validate_variance_column_requires_variance_refs(self):
        """Test that variance column requires variance references."""
        with self.assertRaises(ValidationError):
            self.env['addin.financial.report.column'].create({
                'report_id': self.report.id,
                'sequence': 20,
                'column_type': 'budget_period',
                'column_value': '0',
                'period_count': 1,
            })

    def test_onchange_column_type_actual(self):
        """Test onchange for actual column type clears budget and variance fields."""
        col = self.env['addin.financial.report.column'].new({
            'column_type': 'actual_period',
            'budget_id': self.budget.id,
            'variance_1_seq': 1,
            'variance_2_seq': 2,
        })
        col.onchange_column_type()
        self.assertFalse(col.budget_id, "Budget ID should be reset for 'actual_period'")
        self.assertEqual(col.variance_1_seq, 0, "Variance 1 sequence should be reset to 0 for 'actual_period'")
        self.assertEqual(col.variance_2_seq, 0, "Variance 2 sequence should be reset to 0 for 'actual_period'")

    def test_onchange_column_type_budget(self):
        """Test onchange for budget column type clears variance fields."""
        col = self.env['addin.financial.report.column'].new({
            'column_type': 'budget_period',
            'variance_1_seq': 1,
            'variance_2_seq': 2,
        })
        col.onchange_column_type()
        self.assertEqual(col.variance_1_seq, 0, "Variance 1 sequence should be reset to 0 for 'budget_period'")
        self.assertEqual(col.variance_2_seq, 0, "Variance 2 sequence should be reset to 0 for 'budget_period'")

    def test_onchange_column_type_variance(self):
        """Test onchange for variance column type clears budget field."""
        col = self.env['addin.financial.report.column'].new({
            'column_type': 'variance_period',
            'budget_id': self.budget.id,
        })
        col.onchange_column_type()
        self.assertFalse(col.budget_id)

    def test_date_end_computation(self):
        """Test date end computation for column."""
        col = self.env['addin.financial.report.column'].create({
            'report_id': self.report.id,
            'sequence': 30,
            'column_type': 'actual_period',
            'column_value': '-1',
            'period_count': 1,
        })
        col._date_end()
        expected_date = date.fromisoformat('2025-04-30')
        self.assertEqual(col.date_end, expected_date)

    def test_build_column_name_actual(self):
        """Test building column name for actual period type."""
        col = self.env['addin.financial.report.column'].create({
            'report_id': self.report.id,
            'sequence': 40,
            'column_type': 'actual_period',
            'column_value': '-2',
            'period_count': 2,
        })
        col._date_end()
        name = col.build_column_name()
        self.assertIn('Actual', name, "Column name should contain 'Actual'")
        self.assertIn('Mths to', name, "Column name should contain 'Mths to'")


