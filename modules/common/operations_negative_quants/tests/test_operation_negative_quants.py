# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase,tagged


@tagged('operations_negative_quants')
class TestStockQuantNegativeHandling(TransactionCase):

    def setUp(self):
        super(TestStockQuantNegativeHandling, self).setUp()
        self.location_internal = self.ref('stock.location_refrigerator_small')
        self.product = self.ref('product.product_product_10')
        self.positive_quant = self.env['stock.quant'].create({
            'product_id': self.product,
            'location_id': self.location_internal,
            'quantity': 100,
        })
        self.negative_quant = self.env['stock.quant'].create({
            'product_id': self.product,
            'location_id': self.location_internal,
            'quantity': -50,
        })

    def test_cron_handle_negative_quants(self):
        """Test the cron_handle_negative_quants method to ensure negative quants are handled properly."""
        self.assertEqual(self.positive_quant.quantity, 100, "Initial positive quant quantity should be 100")
        self.assertEqual(self.negative_quant.quantity, -50, "Initial negative quant quantity should be -50")
        self.env['stock.quant'].cron_handle_negative_quants()
        self.assertEqual(self.positive_quant.quantity, 50, "Positive quant quantity should be reduced to 50")
        self.assertEqual(self.negative_quant.quantity, 0, "Negative quant quantity should be eliminated")
