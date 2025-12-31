# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('common', 'operations_nzpost')
class TestEshipIntegration(TransactionCase):
    def setUp(self):
        super(TestEshipIntegration, self).setUp()
        self.delivery_carrier = self.env['delivery.carrier'].create({
            'name': 'eShip Carrier',
            'delivery_type': 'eship',
            'product_id': self.env.ref('delivery.product_product_delivery').id
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'street': '123 Test Street',
            'city': 'Test City',
            'zip': '12345',
            'country_id': self.env.ref('base.us').id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'weight': 1.5,
        })
        self.picking_type = self.env['stock.picking.type'].create({
            'sequence_code': 'TEST',
            'name': 'Test Picking Type',
            'code': 'outgoing',
            'warehouse_id': self.env.ref('stock.warehouse0').id,
        })
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type.id,
            'carrier_id': self.delivery_carrier.id,
        })

    def test_picking_is_eship(self):
        """Test the computed field `is_eship`."""
        self.assertTrue(self.picking.is_eship, "Picking should be marked as eShip.")

    def test_delivery_carrier_eship(self):
        """Test the `delivery.carrier` model for eShip-specific behavior."""
        self.assertEqual(self.delivery_carrier.delivery_type, 'eship', "Delivery type should be set to eShip.")

    def test_create_shipment(self):
        """Test creation of an eShip shipment."""
        eship_shipment = self.env['eship.carrier.shipment'].create({
            'picking_id': self.picking.id,
        })
        self.assertEqual(eship_shipment.picking_id, self.picking, "Shipment should be linked to the picking.")
        self.assertTrue(eship_shipment.eship_order_id, "eShip Order ID should be computed.")

    def test_update_shipment(self):
        """Test updating an eShip shipment."""
        eship_shipment = self.env['eship.carrier.shipment'].create({
            'picking_id': self.picking.id,
        })
        # Simulate fetching shipment data from API
        eship_shipment.json_get = '{"order_status": "Delivered", "tracking_events": []}'
        eship_shipment.eship_order_number = "123456"
        eship_shipment.update_shipment()
        self.assertEqual(eship_shipment.delivery_status, 'Delivered', "Shipment status should be updated.")

    def test_return_shipment_unsupported(self):
        """Test that return shipments raise an error."""
        eship_shipment = self.env['eship.carrier.shipment'].create({
            'picking_id': self.picking.id,
        })
        with self.assertRaises(UserError):
            eship_shipment.create_return_shipment(eship_shipment, None)
