# -*- coding: utf-8 -*-
from odoo.addons.base_testing.tests.transaction_case import EziTransactionCase

from odoo.tests.common import tagged


@tagged("common", "product_multi_company")
class ProductTest(EziTransactionCase):

    def setUp(self):
        super(ProductTest, self).setUp()
        self.product_1 = self.env.ref("product.expense_hotel")

    def tearDown(self):
        super(ProductTest, self).tearDown()

    def currency(self):
        self.assertEqual(self.product_1.currency_id, self.env.company.currency_id)
