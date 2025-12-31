import datetime

from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged


@tagged("common", "account_trial_balance")
class TestAccountTrialBalanceExport(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'fiscalyear_last_month': '12',
            'fiscalyear_last_day': '31',
        })
        # Set the company in the environment
        self.env.user.company_id = self.company

        # Create accounts
        self.account_income = self.env['account.account'].create({
            'name': 'Income Account',
            'code': 'INCOME',
            'account_type': 'income',
            'company_id': self.company.id,
        })
        self.account_expense = self.env['account.account'].create({
            'name': 'Expense Account',
            'code': 'EXPENSE',
            'account_type': 'expense',
            'company_id': self.company.id,
        })
        self.account_asset = self.env['account.account'].create({
            'name': 'Asset Account',
            'code': 'ASSET',
            'account_type': 'asset',
            'company_id': self.company.id,
        })

        # Create journal
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'code': 'TSTJ',
            'type': 'general',
            'company_id': self.company.id,
        })

        # Create account moves
        self.move = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'date': datetime.date(2025, 4, 15),
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_income.id,
                    'debit': 0.0,
                    'credit': 1000.0,
                }),
                (0, 0, {
                    'account_id': self.account_expense.id,
                    'debit': 500.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': self.account_asset.id,
                    'debit': 500.0,
                    'credit': 0.0,
                }),
            ],
        })
        self.move.action_post()

    def test_get_account_year(self):
        wizard = self.env['account.trial.balance.export'].create({
            'as_at_date': datetime.date(2025, 4, 30),
            'report_output': 'xls',
        })
        start_date, end_date, this_month_start = wizard._get_account_year()
        self.assertEqual(start_date, '2025-01-01')
        self.assertEqual(end_date, '2025-12-31')
        self.assertEqual(this_month_start, '2025-04-01')

    def test_get_income_and_exp(self):
        wizard = self.env['account.trial.balance.export'].create({
            'as_at_date': datetime.date(2025, 4, 30),
            'report_output': 'xls',
        })
        start_date, end_date, this_month_start = wizard._get_account_year()
        company_list = str(self.company.id)
        rows = wizard.get_income_and_exp(start_date, end_date, this_month_start, 60, company_list)
        self.assertTrue(any(row[0] == 'INCOME' for row in rows))
        self.assertTrue(any(row[0] == 'EXPENSE' for row in rows))

    def test_get_balance_sheet(self):
        wizard = self.env['account.trial.balance.export'].create({
            'as_at_date': datetime.date(2025, 4, 30),
            'report_output': 'xls',
        })
        start_date, end_date, this_month_start = wizard._get_account_year()
        company_list = str(self.company.id)
        rows = wizard.get_balance_sheet(start_date, end_date, this_month_start, 60, company_list)
        self.assertTrue(any(row[0] == 'ASSET' for row in rows))

    def test_button_process_xls(self):
        wizard = self.env['account.trial.balance.export'].create({
            'as_at_date': datetime.date(2025, 4, 30),
            'report_output': 'xls',
        })
        action = wizard.button_process()
        self.assertIn('res_id', action)
        self.assertEqual(action['res_id'], wizard.id)
        self.assertTrue(wizard.data)
