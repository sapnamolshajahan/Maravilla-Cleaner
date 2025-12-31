# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase, tagged
from datetime import datetime

_logger = logging.getLogger(__name__)

@tagged("common", "purchase_update_linked_sol")
class TestSaleOrderLine(TransactionCase):
    def setUp(self):
        super(TestSaleOrderLine, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product Sale',
            'type': 'consu',
            'list_price': 100.0,
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Test Customer'}).id,
        })
        self.sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0,
        })

    def test_purchase_order_field(self):
        """Test that the purchase_order field is functional."""

        self.assertFalse(self.sale_order_line.purchase_order, "Purchase Order should initially be empty.")

        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Test Supplier'}).id,
        })
        self.sale_order_line.purchase_order = purchase_order
        self.assertEqual(self.sale_order_line.purchase_order, purchase_order,
                         "Purchase Order should match the assigned value.")

    def test_prepare_procurement_values(self):
        """Test the _prepare_procurement_values method."""
        procurement_values = self.sale_order_line._prepare_procurement_values()

        self.assertIn('sale_line_id', self.env.context, "The 'sale_line_id' key should be in the context.")
        self.assertEqual(self.env.context['sale_line_id'], self.sale_order_line.id,
                         "The 'sale_line_id' value in the context should match the sale order line ID.")

        self.assertIsInstance(procurement_values, dict,
                              "The return value of _prepare_procurement_values should be a dictionary.")