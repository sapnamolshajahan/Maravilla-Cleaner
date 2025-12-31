from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged('operations_stocktake')
class TestStockInventoryProduct(TransactionCase):

    def setUp(self):
        super(TestStockInventoryProduct, self).setUp()
        self.product_serial = self.env['product.product'].create({
            'name': 'Test Serial Product',
            'tracking': 'serial',
        })
        self.product_none = self.env['product.product'].create({
            'name': 'Test Non-Serial Product',
            'tracking': 'none',
        })
        self.lot_start = self.env['stock.lot'].create({'name': '0001','product_id':self.product_serial.id})
        self.lot_end = self.env['stock.lot'].create({'name': '0005','product_id':self.product_serial.id})

    def test_validate_serial_range(self):
        """Test serial range validation logic"""
        model = self.env['stocktake.data.entry.line']
        self.assertTrue(
            model.validate_serial_range(self.lot_start, self.lot_end, 5),
            "Serial range validation failed for correct range"
        )
        self.assertFalse(
            model.validate_serial_range(self.lot_start, self.lot_end, 6),
            "Serial range validation passed for incorrect range"
        )
        self.assertTrue(
            model.validate_serial_range(self.lot_start, None, 1),
            "Serial range validation failed for quantity 1 with no end lot"
        )

    def test_validate_line(self):
        """Test the validate_line constraint"""
        line = self.env['stocktake.data.entry.line'].create({
            'product_id': self.product_serial.id,
            'quantity': 5,
            'production_lot_id': self.lot_start.id,
            'end_production_lot': self.lot_end.id,
        })
        with self.assertRaises(ValidationError):
            line.quantity = -1
            line.validate_line()

        with self.assertRaises(ValidationError):
            line.quantity = 6
            line.validate_line()

    def test_onchange_product(self):
        """Test the onchange_product logic"""
        line = self.env['stocktake.data.entry.line'].new({
            'product_id': self.product_serial.id,
        })
        line.onchange_product()
        self.assertTrue(line.serialised, "Serialised field not set correctly for serial-tracked product")

        line.product_id = self.product_none
        line.onchange_product()
        self.assertFalse(line.serialised, "Serialised field incorrectly set for non-serial product")

    def test_onchange_serialise(self):
        """Test the onchange_serialise logic"""
        line = self.env['stocktake.data.entry.line'].new({
            'product_id': self.product_serial.id,
            'serialised': True,
            'quantity': 0,
        })
        res = line.onchange_serialise()
        self.assertIn('warning', res, "Warning not triggered for invalid quantity")
        self.assertEqual(res['value']['quantity'], 1, "Quantity not reset to minimum for serialised product")
        line.quantity = 5
        line.production_lot_id = self.lot_start
        line.end_production_lot = self.lot_end
        res = line.onchange_serialise()
        self.assertNotIn('warning', res, "Incorrect warning triggered for valid serial range")
