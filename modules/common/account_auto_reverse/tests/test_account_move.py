# -*- coding: utf-8 -*-

from datetime import datetime, date

from odoo.exceptions import UserError
from odoo.tests.common import tagged, TransactionCase


@tagged('common', 'account_auto_reverse')
class TestAccountMoveReversal(TransactionCase):

    def setUp(self):
        super(TestAccountMoveReversal, self).setUp()

        # Create a test journal
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'code': 'TEST',
            'type': 'general',
            'company_id': self.env.company.id
        })

        # Create a test account move
        self.account_move = self.env['account.move'].create({
            'ref': 'TEST REF',
            'journal_id': self.journal.id,
            'date': datetime.today().date(),
            'reversal_accounting_date': self.get_date_expected(),
            'line_ids': [
                (0, 0, {
                    "account_id": self.env["account.account"].create(
                        {
                            "name": "Test Account",
                            "code": "TESTACC",
                            "account_type": "liability_payable",
                            "reconcile": True
                        }).id,
                    "debit": 100.0,
                    "credit": 0.0
                }),
                (0, 0, {
                    "account_id": self.env["account.account"].create(
                        {
                            "name": "Test Account 2",
                            "code": "TESTACC2",
                            "account_type": "liability_payable",
                            "reconcile": True
                        }).id,
                    "debit": 0.0,
                    "credit": 100.0
                })
            ]
        })

    def test_onchange_auto_reverse(self):
        """Test that the reversal accounting date is correctly set."""
        self.account_move.auto_reverse = True
        self.account_move.onchange_auto_reverse()
        expected_date = self.get_date_expected(self.account_move)
        self.assertEqual(self.account_move.reversal_accounting_date, expected_date,
                         "Reversal accounting date is incorrect.")

    def test_auto_reverse_move(self):
        """Test the creation of an auto-reversed move."""
        reversed_move = self.account_move._auto_reverse_move(date=self.get_date_expected(self.account_move))

        self.assertEqual(reversed_move.reversal_of_move_id, self.account_move,
                         "Reversal move does not reference the original move.")
        self.assertEqual(reversed_move.date, self.account_move.reversal_accounting_date,
                         "Reversal date does not match expected date.")

        for line in reversed_move.line_ids:
            original_line = self.account_move.line_ids.filtered(lambda l: l.account_id == line.account_id)
            self.assertEqual(line.debit, original_line.credit,
                             "Reversed line debit does not match original line credit.")
            self.assertEqual(line.credit, original_line.debit,
                             "Reversed line credit does not match original line debit.")

    def test_check_auto_reverse(self):
        """Test the automatic reversal during posting."""
        self.account_move.auto_reverse = True
        self.account_move.action_post()

        reversed_move = self.account_move.reverse_move_id
        self.assertTrue(reversed_move, "Reversed move was not created.")
        self.assertEqual(reversed_move.reversal_of_move_id, self.account_move,
                         "Reversed move does not reference the original move.")
        self.assertEqual(reversed_move.state, 'posted', "Reversed move was not posted.")

    def test_prevent_multiple_reversals(self):
        """Ensure UserError is raised if trying to create multiple reversals."""
        self.account_move.auto_reverse = True
        self.account_move.action_post()

        with self.assertRaises(UserError):
            self.account_move.check_auto_reverse()

    def test_get_reversal_date(self):
        """Test the calculation of the reversal date."""
        reversal_date = self.account_move.get_reversal_date()
        expected_date = self.get_date_expected(self.account_move)
        self.assertEqual(reversal_date, expected_date, "Calculated reversal date is incorrect.")

    def get_date_expected(self, move=False):
        journal_date = move.date if move else datetime.today().date()
        year = journal_date.year
        month = journal_date.month + 1

        if month == 13:
            year += 1
            month = 1

        day = 1
        expected_date = date(year, month, day)
        return expected_date
