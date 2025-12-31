# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged


_logger = logging.getLogger(__name__)


@tagged("common", "sale_generic_changes")
class TestSaleOrder(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Create the required records for testing
        self.partner = self.env.ref('base.partner_demo')
        self.sale_order = self.env['sale.order'].create({'name': 'Test SO','partner_id': self.partner.id})
        self.so_line1 = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'sequence': 20,
            'name': 'Product 1',
        })
        self.so_line2 = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'sequence': 10,
            'name': 'Product 2',
        })

        # Create a SaleOrderSort record
        self.sale_order_sort = self.env['sale.order.sort'].create({
            'sale_order': self.sale_order.id,
            'lines': [
                (0, 0, {'sale_order_line': self.so_line1.id, 'sequence': self.so_line1.sequence}),
                (0, 0, {'sale_order_line': self.so_line2.id, 'sequence': self.so_line2.sequence}),
            ],
        })

    def test_update_sequence(self):
        """Test that the update_sequence method correctly updates line sequences."""
        self.sale_order_sort.update_sequence()
        # Fetch updated lines
        updated_line1 = self.so_line1.read(['sequence'])[0]['sequence']
        updated_line2 = self.so_line2.read(['sequence'])[0]['sequence']
        # Assert the sequences are updated correctly
        self.assertEqual(updated_line1, 20, "The first line's sequence should be updated to 20.")
        self.assertEqual(updated_line2, 10, "The second line's sequence should be updated to 10.")
