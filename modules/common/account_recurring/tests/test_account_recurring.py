# -*- coding: utf-8 -*-
import datetime
from odoo.tests.common import TransactionCase,tagged

@tagged('account_recurring')
class TestAccountRecurring(TransactionCase):
    def setUp(self):
        super(TestAccountRecurring, self).setUp()
        self.move = self.env['account.move'].create({
            'name': 'Test Move',
            'date': datetime.date.today(),
            'move_type': 'entry',
        })

        self.recurring = self.env['account.recurring'].create({
            'name': 'Test Recurring',
            'move': self.move.id,
            'interval': 'week',
            'frequency': 1,
            'start_date': datetime.date.today() - datetime.timedelta(weeks=2),
            'last_run_date': datetime.date.today() - datetime.timedelta(weeks=1),
        })
    def test_run_recurring_weekly(self):
        """Test that recurring journals are correctly run on a weekly basis."""
        today = datetime.date.today()
        self.recurring.run_recurring()
        lines = self.env['account.recurring.line'].search([('account_recurring', '=', self.recurring.id)])
        self.assertTrue(lines, "No recurring lines were created")
        self.assertEqual(lines[0].date, today, "The recurring line date is incorrect")

    def test_run_recurring_monthly(self):
        """Test that recurring journals are correctly run on a monthly basis."""
        self.recurring.write({
            'interval': 'month',
            'frequency': 1,
            'monthly_value': 'first',
            'start_date': datetime.date.today() - datetime.timedelta(days=100),
            'last_run_date': datetime.date.today() - datetime.timedelta(days=60)
        })
        today = datetime.date.today()
        self.recurring.run_recurring()
        lines = self.env['account.recurring.line'].search([('account_recurring', '=', self.recurring.id)])
        self.assertTrue(lines, "No recurring lines were created")
        self.assertEqual(lines[0].date, today, "The recurring line date is incorrect")

    def test_clone_me(self):
        """Test the clone_me method."""
        today = datetime.date.today()
        self.recurring.clone_me(self.recurring, today)
        cloned_moves = self.env['account.move'].search([('ref', '=', self.recurring.name)])
        self.assertTrue(cloned_moves, "No cloned moves were created")
        self.assertEqual(cloned_moves[0].date, today, "The cloned move date is incorrect")
