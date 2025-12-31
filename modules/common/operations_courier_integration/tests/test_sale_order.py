from odoo.tests.common import TransactionCase
from odoo.tools import float_compare, float_round
import logging

from odoo.odoo.tests import tagged

_logger = logging.getLogger(__name__)

@tagged("operations_courier_integration")
class TestSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service'
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test Carrier',
            'price_unit_rounding_digits': 0.01,
            "product_id": self.product.id
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'is_company': True,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id
        })
        self.sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 10.0
        })

    def test_create_delivery_line(self):
        """Test _create_delivery_line for correct rounding and naming"""
        price_unit = 12.3456
        rounded_price = float_round(price_unit, precision_rounding=self.carrier.price_unit_rounding_digits)

        delivery_line = self.sale_order._create_delivery_line(self.carrier, price_unit)

        self.assertEqual(delivery_line.price_unit, rounded_price, "Price unit should be correctly rounded")
        self.assertFalse("Estimate" in delivery_line.name, "Estimate should be removed from the name")

        self.assertNotEqual(delivery_line.price_unit, 0, "Price unit should not be zero")

    def test_write_price_rounding(self):
        """Test price rounding in Sale Order Line write method"""
        precision = 0.05
        new_price = 12.3456
        rounded_price = float_round(new_price, precision_rounding=precision)

        self.sale_order_line.with_context(CONTEXT_SALE_LINE_PRICE_ROUNDING=precision).write({'price_unit': new_price})

        self.assertEqual(
            self.sale_order_line.price_unit, rounded_price,
            "Price unit should be rounded according to the provided precision"
        )

    def test_write_other_fields(self):
        """Test that other fields update correctly"""
        self.sale_order_line.write({'product_uom_qty': 2})
        self.assertEqual(self.sale_order_line.product_uom_qty, 2, "Product quantity should update correctly")
