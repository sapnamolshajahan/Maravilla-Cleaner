# -*- coding:utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('res_partner_credit_limit')
class TestResPartner(TransactionCase):
    def setUp(self):
        super(TestResPartner, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'customer_rank': 1,
            'credit_limit': 5000.0,
            'credit': 1000.0,
        })
        self.product_template = self.env['product.template'].create({
            'name': 'Test Product',
            'type': 'consu',
            'base_unit_count': 1,
        })
        self.company = self.env['res.company'].search([], limit=1)
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'product_tmpl_id': self.product_template.id,
            'is_storable': 'True',
            'list_price': 100.0,
            'type': "service",
            'company_id': self.company.id,
        })

        self.account_move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'state': 'draft',
            'amount_total': 2000,
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'invoice_status': 'to invoice',
        })

        self.sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,  # Default product
            'product_uom_qty': 1,
            'price_unit': 500,
            'invoice_status': 'to invoice',
        })

    def test_calculate_remaining_credit(self):
        """Test the `calculate_remaining_credit` method."""
        remaining_credit = self.partner.calculate_remaining_credit()
        expected_remaining_credit = (
                self.partner.credit_limit - self.partner.credit - 500
        )
        self.assertEqual(
            remaining_credit,
            expected_remaining_credit,
            "Remaining credit calculation should match the expected value."
        )


    def test_get_total_receivable(self):
        """Test the computation of total receivable and credit remaining."""
        self.partner._get_total_receivable()
        self.assertEqual(self.partner.total_receivable, self.partner.credit, "Total receivable is not set correctly")
        expected_credit_remaining = self.partner.calculate_remaining_credit()
        self.assertEqual(self.partner.credit_remaining, expected_credit_remaining, msg="Credit remaining is not set correctly")
        """Test behavior when there is no credit limit."""
        self.partner.credit_limit = 0.0
        self.partner._get_total_receivable()
        self.assertEqual(self.partner.total_receivable, 0.0, "Total receivable should be zero when credit limit is zero")
        self.assertEqual(self.partner.credit_remaining, 0.0, "Credit remaining should be zero when credit limit is zero")

    def test_credit_debit_get(self):
        """Test the `_credit_debit_get` method without searching for values."""
        receivable_account = self.env['account.account'].create({
            'name': 'Receivable',
            'code': 'RCV',
            'account_type': 'asset_receivable',
        })

        payable_account = self.env['account.account'].create({
            'name': 'Payable',
            'code': 'PYB',
            'account_type': 'asset_receivable',
        })

        self.env['account.move.line'].create([
            {
                'partner_id': self.partner.id,
                'account_id': receivable_account.id,
                'amount_residual': 1000,
                'parent_state': 'posted',
                'move_id': self.account_move.id,
            },
            {
                'partner_id': self.partner.id,
                'account_id': payable_account.id,
                'amount_residual': -500,
                'parent_state': 'posted',
                'move_id': self.account_move.id,
            },
        ])
        self.partner._credit_debit_get()
        self.assertAlmostEqual(
            self.partner.credit,
            0,
            "Credit should be updated based on receivable account move lines."
        )
        self.assertAlmostEqual(
            self.partner.debit,
            0,
            "Debit should be updated based on payable account move lines."
        )