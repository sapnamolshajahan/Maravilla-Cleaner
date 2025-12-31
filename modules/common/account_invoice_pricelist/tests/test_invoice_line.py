# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.addons.base.tests.common import SavepointCaseWithUserDemo

@tagged("common", "account_invoice_pricelist")
class TestAccountInvoiceLinePriceUnit(SavepointCaseWithUserDemo):

    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoiceLinePriceUnit, cls).setUpClass()

        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist',
            'currency_id': cls.env.ref('base.USD').id,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })

        cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '3_global',
            'product_id': cls.product.id,
            'fixed_price': 80.0,
        })

        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'pricelist': cls.pricelist.id,
        })

        cls.invoice_line = cls.env['account.move.line'].create({
            'move_id': cls.invoice.id,
            'product_id': cls.product.id,
            'quantity': 1.0,
        })

    def test_compute_price_unit(self):
        """Test price unit computation and discount calculation."""

        self.invoice_line._compute_price_unit()

        expected_price_unit = self.product.list_price
        expected_discount = ((self.product.list_price - 80.0) / self.product.list_price) * 100

        self.assertEqual(
            self.invoice_line.price_unit,
            expected_price_unit,
            "Price unit should be set to the product's list price."
        )
        self.assertAlmostEqual(
            self.invoice_line.discount,
            expected_discount,
            msg="Discount should be correctly calculated based on the pricelist and list price."
        )

    def test_compute_price_unit_no_list_price(self):
        """Test discount calculation when product has no list price."""
        product_no_list_price = self.env['product.product'].create({
            'name': 'Product No List Price',
            'list_price': 0.0,
        })

        invoice_line_no_list_price = self.env['account.move.line'].create({
            'move_id': self.invoice.id,
            'product_id': product_no_list_price.id,
            'quantity': 1.0,
        })

        invoice_line_no_list_price._compute_price_unit()

        self.assertEqual(
            invoice_line_no_list_price.discount,
            0.0,
            "Discount should be 0.0 when the product's list price is 0.0."
        )

