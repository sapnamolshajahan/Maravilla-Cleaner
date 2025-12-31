# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import tagged
from .common import AccountForwardExchangeSPC


@tagged("common", "account_forward_exchange")
class TestAccountForwardExchange(AccountForwardExchangeSPC):
    """
    Remember the test DB demo data has EUR and USD currencies enabled and the company currency is USD.
    You cannot change a company's currency if any journal entries exists

    Also, when adding product lines onto a foreign currency invoice, the standard_price is used and converted to the
    foreign currency amount using the floating exchange rate. The FEC rate only affects the accounting entries.
    """

    @classmethod
    def setUpClass(cls):
        super(TestAccountForwardExchange, cls).setUpClass()

    def setUp(self):
        super(TestAccountForwardExchange, self).setUp()

    def test_fec_create(self):
        fec = self._create_fec(contract_no='1234', amount=1000, rate=1.4)

        # Confirm default state
        self.assertEqual(fec.state, 'in-progress')

        # Confirm the auto sequence is working
        self.assertTrue(fec.name)

        # Confirm if amount commited is zero
        self.assertEqual(fec.amount_committed, 0.0)

    def test_fec_validation(self):
        fec = self._create_fec(contract_no='1234', amount=1000, rate=1.4)

        with self.assertRaisesRegex(ValidationError, 'Contract amount must be a positive non-zero number'):
            with Form(fec) as f:
                f.amount = 0

        with self.assertRaisesRegex(ValidationError, 'Contract amount must be a positive non-zero number'):
            with Form(fec) as f:
                f.amount = -1

        with self.assertRaisesRegex(ValidationError, 'Rate must be a positive non-zero number'):
            with Form(fec) as f:
                f.rate = 0

        with self.assertRaisesRegex(ValidationError, 'Rate must be a positive non-zero number'):
            with Form(fec) as f:
                f.rate = -0.1

        with self.assertRaisesRegex(ValidationError, 'Due Date cannot be earlier than Entered Date'):
            with Form(fec) as f:
                f.contract_enter_date = fields.Date.today()
                f.due_date = fields.Date.today() - timedelta(days=1)

        # Testing required fields
        with self.assertRaises(AssertionError):
            with Form(fec) as f:
                f.currency = False

        with self.assertRaises(AssertionError):
            with Form(fec) as f:
                f.contract_no = False

        with self.assertRaises(AssertionError):
            with Form(fec) as f:
                f.contract_enter_date = False

        with self.assertRaises(AssertionError):
            with Form(fec) as f:
                f.due_date = False

    def xx_test_fec_committed_amount(self):
        fec = self._create_fec(contract_no='1234', amount=10, rate=1.4)
        inv_form = self._make_supplier_invoice_form()

        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec
            fec_line.amount_allocated = 9

        inv = inv_form.save()

        self.assertEqual(fec.amount_committed, 9)

        inv.fec_lines[0].amount_allocated = 10

        #  Needed because compute method uses SQL
        fec._invalidate_cache()
        self.assertEqual(fec.amount_committed, 10)

        inv_form2 = self._make_supplier_invoice_form()
        with inv_form2.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form2.fec_lines.new() as fec_line:
            fec_line.fec = fec
            fec_line.amount_allocated = 10

        inv_form2.save()
        fec._invalidate_cache()
        self.assertEqual(fec.amount_committed, 20)
        self.assertTrue(fec.overcommitted)
