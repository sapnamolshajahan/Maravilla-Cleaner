from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.odoo.tests import tagged


@tagged("operations_courier_integration")
class TestStockPicking(TransactionCase):
    def setUp(self):
        super(TestStockPicking, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': 'True',
            'list_price': 100.0,
            'type': "service",
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test Carrier',
            'delivery_type': 'fixed',
            'ship_after_validation': True,
            'product_id': self.product.id
        })

        self.picking_type = self.env['stock.picking.type'].create({
            'name': 'Test Picking Type',
            'code': 'outgoing',
            'sequence_code': 'M02'
        })
        self.picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'carrier_id': self.carrier.id,
        })


    def test_compute_carrier_integration(self):
        self.picking._compute_carrier_integration()
        self.assertFalse(self.picking.has_carrier_integration, "Carrier integration should be False initially.")

        self.carrier.delivery_type = 'fixed'
        self.picking._compute_carrier_integration()
        self.assertFalse(self.picking.has_carrier_integration,
                         "Carrier integration should still be False when delivery_type is 'fixed'.")

    def test_button_download_courier_labels_no_shipment(self):
        with self.assertRaises(UserError, msg="No carrier shipment linked to picking"):
            self.picking.button_download_courier_labels()


    def test_action_validate_and_ship_success(self):
        self.picking.picking_type_id.code = 'outgoing'
        result = self.picking.action_validate_and_ship()

        self.assertEqual(result['res_model'], 'carrier.shipment.wizard',
                         "The 'res_model' should be 'carrier.shipment.wizard'.")
        self.assertEqual(result['target'], 'new', "The 'target' should be 'new'.")

    def test_action_ship_only_success(self):
        self.picking.picking_type_id.code = 'outgoing'
        result = self.picking.action_ship_only()
        self.assertEqual(result['res_model'], 'carrier.shipment.wizard',
                         "Expected 'res_model' to be 'carrier.shipment.wizard'")
        self.assertEqual(result['target'], 'new', "Expected 'target' to be 'new'")

    def test_send_to_shipper(self):
        self.picking.carrier_id.delivery_type = 'fixed'
        self.picking.carrier_price = 0.0
        result = self.picking.send_to_shipper()
        self.assertIsNone(result, "Expected 'send_to_shipper' to return None, but got a non-None result.")

    def test_button_reprint_courier_labels_no_shipment(self):
        with self.assertRaises(UserError, msg="This delivery does not have a Carrier Shipment attached"):
            self.picking.button_reprint_courier_labels()


