# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import UserError
from odoo.tests import common, tagged
from .common import TestAccountCommonPayment

_logger = logging.getLogger(__name__)


@tagged("common", "account_payment_remittance_advice")
class TestAccountPayment(TestAccountCommonPayment):
    """Class to test account payment workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()

    def test_get_remittance_report(self):
        report = self.env['account.payment'].get_remittance_report()
        self.assertEqual(report, self.env.ref('account_payment_remittance_advice.payment_remittance_advice'))

    def test_action_email_remittance_order_no_active_ids(self):
        with self.assertRaises(UserError):
            self.env['account.payment'].with_context(active_ids=None).action_email_remittance_order()

    def test_action_email_remittance_order(self):
        action = self.env['account.payment'].with_context(
            active_ids=[self.payment1.id, self.payment2.id]).action_email_remittance_order()
        wizard = self.env['remittance.advice.choose.partner'].browse(action['res_id'])
        self.assertEqual(len(wizard.lines), 2)
        self.assertEqual(wizard.lines[0].partner_id, self.partner2)
        self.assertEqual(wizard.lines[1].partner_id, self.partner1)

    def test_remittance_order_print(self):
        # Call the remittance_order_print method
        action = self.payment1.remittance_order_print()
        self.assertEqual(action["name"], "Remittance Advice", "The name of the action is incorrect.")
        self.assertIn(action["report_name"], 'account_payment_remittance_advice.payment_remittance_advice')
