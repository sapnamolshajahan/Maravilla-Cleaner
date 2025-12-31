# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged, Form
from odoo.tools import float_round
from .common import AccountForwardExchangeSPC


@tagged("common", "account_forward_exchange")
class TestSupplierInvoice(AccountForwardExchangeSPC):

    @classmethod
    def setUpClass(cls):
        super(TestSupplierInvoice, cls).setUpClass()

    def setUp(self):
        super(TestSupplierInvoice, self).setUp()

    def xx_test_supplier_invoice_no_fec(self):
        inv_form = self._make_supplier_invoice_form()
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form.invoice_line_ids.new() as line2:
            line2.product_id = self.product_2
            line2.account_id = self.account

        inv = inv_form.save()

        self.assertEqual(inv.currency_id, self.currency_nzd, msg="Currency not the same after invoice create")

        expected_total = (line1.product_id.standard_price + line2.product_id.standard_price) * self.currency_nzd.rate

        self.assertEqual(inv.amount_untaxed, expected_total, msg="Invoice currency total invalid")
        total_debit = sum(inv.line_ids.mapped('debit'))
        expected_debit = line1.product_id.standard_price + line2.product_id.standard_price + \
                         (inv.amount_tax_signed * -1)

        self.assertEqual(total_debit, expected_debit, msg="Accounting entries currency conversion incorrect")
        inv.action_post()

        total_debit_after_post = sum(inv.line_ids.mapped('debit'))
        self.assertEqual(total_debit_after_post, expected_debit, msg="Accounting entries changed after posting")

    def xx_test_supplier_invoice_with_fec_full_allocation(self):
        fec1 = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        fec2 = self._create_fec(contract_no='4321', amount=1000, rate=1.6)
        inv_form = self._make_supplier_invoice_form()
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form.invoice_line_ids.new() as line2:
            line2.product_id = self.product_2
            line2.account_id = self.account

        line_totals = line1.product_id.standard_price + line2.product_id.standard_price
        expected_nzd_total = line_totals * self.currency_nzd.rate
        allocate_amount_1 = 1000
        allocate_amount_2 = expected_nzd_total - allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec1
            # onchange should have triggered to default allocate amount
            self.assertAlmostEqual(fec_line.amount_allocated, inv_form.amount_untaxed, places=2,
                                   msg="Default Allocate amount must be equal to invoice untaxed amount")
            fec_line.amount_allocated = allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec2
            fec_line.amount_allocated = allocate_amount_2

        inv = inv_form.save()

        expected_blended_rate = ((fec1.rate * allocate_amount_1) + (fec2.rate * allocate_amount_2)) / inv.amount_untaxed
        expected_blended_rate = float_round(expected_blended_rate, precision_digits=4)
        self.assertAlmostEqual(inv.currency_rate, expected_blended_rate, places=4,
                               msg="Computed blended currency rate incorrect or decimal precision mismatch")

        total_debit = sum(inv.line_ids.mapped('debit'))
        expected_debit = inv.amount_total / expected_blended_rate

        self.assertAlmostEqual(total_debit, expected_debit, places=2,
                               msg="Accounting entries currency conversion incorrect")

        inv.action_post()

        total_debit_after_post = sum(inv.line_ids.mapped('debit'))
        self.assertAlmostEqual(total_debit_after_post, expected_debit,
                               places=2, msg="Accounting entries changed after posting")

    def xx_test_supplier_invoice_with_fec_semi_allocation(self):
        fec1 = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        inv_form = self._make_supplier_invoice_form()
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form.invoice_line_ids.new() as line2:
            line2.product_id = self.product_2
            line2.account_id = self.account

        line_totals = line1.product_id.standard_price + line2.product_id.standard_price
        expected_nzd_total = line_totals * self.currency_nzd.rate
        allocate_amount_1 = 1000
        allocate_amount_2 = expected_nzd_total - allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec1
            fec_line.amount_allocated = allocate_amount_1

        inv = inv_form.save()

        expected_blended_rate = ((fec1.rate * allocate_amount_1) + (self.currency_nzd.rate * allocate_amount_2)
                                 ) / inv.amount_untaxed

        expected_blended_rate = float_round(expected_blended_rate, precision_digits=4)
        self.assertAlmostEqual(inv.currency_rate, expected_blended_rate, places=4,
                               msg="Computed blended currency rate incorrect or decimal precision mismatch")

        total_debit = sum(inv.line_ids.mapped('debit'))
        expected_debit = inv.amount_total / expected_blended_rate

        self.assertAlmostEqual(total_debit, expected_debit, places=2,
                               msg="Accounting entries currency conversion incorrect")

        inv.action_post()

        total_debit_after_post = sum(inv.line_ids.mapped('debit'))
        self.assertAlmostEqual(total_debit_after_post, expected_debit,
                               places=2, msg="Accounting entries changed after posting")

    def xx_test_supplier_credit_note_from_paid_invoice(self):
        fec1 = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        fec2 = self._create_fec(contract_no='4321', amount=1000, rate=1.6)
        inv_form = self._make_supplier_invoice_form()
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form.invoice_line_ids.new() as line2:
            line2.product_id = self.product_2
            line2.account_id = self.account

        allocate_amount_1 = 1000
        allocate_amount_2 = inv_form.amount_untaxed - allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec1
            fec_line.amount_allocated = allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec2
            fec_line.amount_allocated = allocate_amount_2

        inv = inv_form.save()
        inv.action_post()

        inv.payment_state = 'paid'
        cn = self._create_credit_note_from_supplier_invoice(from_invoice=inv, partial_refund=True)

        self.assertFalse(cn.fec_lines, msg='Credit notes from paid supplier invoice should not have FEC lines')

    def xx_test_supplier_credit_note_from_unpaid_invoice(self):
        fec1 = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        fec2 = self._create_fec(contract_no='4321', amount=1000, rate=1.6)
        inv_form = self._make_supplier_invoice_form()
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with inv_form.invoice_line_ids.new() as line2:
            line2.product_id = self.product_2
            line2.account_id = self.account

        allocate_amount_1 = 1000
        allocate_amount_2 = inv_form.amount_untaxed - allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec1
            fec_line.amount_allocated = allocate_amount_1

        with inv_form.fec_lines.new() as fec_line:
            fec_line.fec = fec2
            fec_line.amount_allocated = allocate_amount_2

        inv = inv_form.save()
        inv.action_post()

        cn = self._create_credit_note_from_supplier_invoice(from_invoice=inv, partial_refund=True)

        self.assertTrue(cn.fec_lines, msg='Credit notes from unpaid supplier invoice must have FEC lines')
        self.assertListEqual(cn.fec_lines.mapped('fec.id'), inv.fec_lines.mapped('fec.id'),
                             msg="FEC of FEC line on CN must be the same as FEC line on Invoice")
        # The allocated amounts on CNs should be negative, hence multiplying with -1 to make positive
        self.assertAlmostEqual(cn.fec_lines[0].amount_allocated * -1, allocate_amount_1, places=2,
                               msg='FEC line allocated amount must be -ve on Credit Notes')
        self.assertAlmostEqual(cn.fec_lines[1].amount_allocated * -1, allocate_amount_2, places=2,
                               msg='FEC line allocated amount must be -ve on Credit Notes')

        # Check that onchange of allocated_amount is made -ve if user inputs positive amount
        with Form(cn) as cn_form:
            with cn_form.fec_lines.edit(0) as fec_line:
                fec_line.amount_allocated = 500
                self.assertEqual(fec_line.amount_allocated, -500.00)

    def test_invoice_fec_line_invoice_over_allocation(self):
        fec = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        inv_form = self._make_supplier_invoice_form()

        with self.assertRaisesRegex(ValidationError, 'Total allocated FEC amounts exceeds'):
            with inv_form.fec_lines.new() as fec_line:
                fec_line.fec = fec
                fec_line.amount_allocated = 100

            inv_form.save()

    def test_invoice_fec_line_contract_over_allocation(self):
        fec = self._create_fec(contract_no='1234', amount=100, rate=1.4)
        inv_form = self._make_supplier_invoice_form()

        #  Add a line to make sure invoice amount is non-zero
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with self.assertRaisesRegex(UserError, "Amount allocated cannot exceed the amount unallocated on the contract"):
            with inv_form.fec_lines.new() as fec_line:
                fec_line.fec = fec
                fec_line.amount_allocated = 101

            inv_form.save()

    def test_invoice_fec_line_no_allocation(self):
        fec = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        inv_form = self._make_supplier_invoice_form()

        with self.assertRaisesRegex(ValidationError, 'Must be a non-zero amount'):
            with inv_form.fec_lines.new() as fec_line:
                fec_line.fec = fec
                fec_line.amount_allocated = 0

            inv_form.save()

    def test_invoice_fec_line_duplicate_fecs(self):
        fec = self._create_fec(contract_no='1234', amount=1000, rate=1.4)
        inv_form = self._make_supplier_invoice_form()

        #  Add a line to make sure invoice amount is non-zero
        with inv_form.invoice_line_ids.new() as line1:
            line1.product_id = self.product_1
            line1.account_id = self.account

        with self.assertRaisesRegex(ValidationError, 'A FEC can only be used once on an invoice'):
            with inv_form.fec_lines.new() as fec_line:
                fec_line.fec = fec
                fec_line.amount_allocated = 1
            with inv_form.fec_lines.new() as fec_line:
                fec_line.fec = fec
                fec_line.amount_allocated = 1

            inv_form.save()
