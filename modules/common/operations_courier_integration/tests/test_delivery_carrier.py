from odoo.tests import common
from odoo.odoo.tests import tagged


@tagged('operations_courier_integration')
class TestDeliveryCarrier(common.TransactionCase):
    def setUp(self):

        super().setUp()
        self.DeliveryCarrier = self.env["delivery.carrier"]
        self.Picking = self.env["stock.picking"]
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': 'True',
            'list_price': 100.0,
            'type': "service",
        })
        self.carrier = self.DeliveryCarrier.create({
            "name": "Test Carrier",
            "delivery_type": "fixed",
            "ship_after_validation": True,
            "price_unit_rounding_digits": 0.05,
            "product_id": self.product.id
        })
        self.location = self.env['stock.location'].create({
            'name': 'Customer Location',
            'usage': 'customer',
        })
        self.picking_type = self.env['stock.picking.type'].create({
            'name': 'Test Picking Type',
            'code': 'outgoing',
            'sequence_code': 'TEST_PICK',
        })
        self.picking = self.Picking.create({
            "carrier_id": self.carrier.id,
            "carrier_tracking_ref": "123456789",
            "carrier_price": 100.0,
            "location_id": self.location.id,
            "location_dest_id": self.location.id,
            "picking_type_id": self.picking_type.id,
        })

    def test_write(self):
        """Test that write method correctly updates values and sets invoice policy."""
        self.carrier.write({"delivery_type": "base_on_rule"})
        self.assertEqual(self.carrier.invoice_policy, "estimated")

    def test_create(self):
        """Test that create method correctly sets invoice policy."""
        carrier = self.DeliveryCarrier.create({
            "name": "Fixed Carrier",
            "delivery_type": "fixed",
            "product_id": self.product.id
        })
        self.assertEqual(carrier.invoice_policy, "estimated")


    def test_send_shipping(self):
        """Test that send_shipping returns the correct tracking number and cost."""
        carrier = self.DeliveryCarrier.create({
            "name": "Test Carrier",
            "delivery_type": "fixed",
            "ship_after_validation": True,
            "price_unit_rounding_digits": 0.05,
            "product_id": self.product.id
        })
        result = carrier.send_shipping(self.picking)
        self.assertEqual(result[0]["exact_price"], 100.0)

    def test_fixed_get_tracking_link(self):
        result = self.carrier.fixed_get_tracking_link(self.picking)
        self.assertEqual(result,False, "Tracking link should be False")

