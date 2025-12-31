# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase,tagged

@tagged('product_no_variants')
class TestGenericViewProduct(TransactionCase):

    def setUp(self):
        super(TestGenericViewProduct, self).setUp()
        self.product_template = self.env['product.template'].create({
            'name': 'Test Product Template',
        })
        self.product_variant = self.product_template.product_variant_ids[0]
    def test_purchase_count(self):
        count_result = self.product_variant._purchase_count()
        expected_result = {self.product_variant.id: 0}
        self.assertEqual(count_result, expected_result, "The _purchase_count method should return 0 for all products.")

    def test_rules_count(self):
        count_result = self.product_variant._rules_count()
        expected_result = {self.product_variant.id: 0}
        self.assertEqual(count_result, expected_result, "The _rules_count method should return 0 for all products.")

    def test_sales_count(self):
        count_result = self.product_variant._sales_count()
        expected_result = {self.product_variant.id: 0}
        self.assertEqual(count_result, expected_result, "The _sales_count method should return 0 for all products.")

    def test_stock_move_count(self):
        count_result = self.product_variant._stock_move_count()
        expected_result = {self.product_variant.id: {'reception_count': 0, 'delivery_count': 0}}
        self.assertEqual(count_result, expected_result, "The _stock_move_count method should return 0 for receptions and deliveries.")

    def test_bom_orders_count(self):
        count_result = self.product_template._bom_orders_count()
        expected_result = {self.product_template.id: 0}
        self.assertEqual(count_result, expected_result, "The _bom_orders_count method should return 0 for all product templates.")

    def test_bom_orders_count_mo(self):
        count_result = self.product_template._bom_orders_count_mo()
        expected_result = {self.product_template.id: 0}
        self.assertEqual(count_result, expected_result, "The _bom_orders_count_mo method should return 0 for all product templates.")

    def test_compute_free_qty(self):
        self.product_variant.write({'free_qty': 100.0})
        self.product_template._compute_free_qty()
        self.assertEqual(self.product_template.free_qty, 100.0, "The free_qty on the product template should match the variant's free_qty.")
