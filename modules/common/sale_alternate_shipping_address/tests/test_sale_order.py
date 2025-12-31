# -*- coding: utf-8 -*-
import logging

from io import BytesIO
from odoo.tests import common, tagged
from odoo.exceptions import UserError
import base64
from openpyxl import Workbook

_logger = logging.getLogger(__name__)

@tagged("common", "sale_alternate_shipping_address")
class TestSaleAlternateShippingAddress(common.TransactionCase):
    """Class to test operation related sale.order shipping address workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.country = self.env['res.country'].create({'name': 'Test123', 'code': '345'})
        self.state = self.env['res.country.state'].create({
            'name': 'Auckland',
            'country_id': self.country.id,
            'code': '123'
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'order_line': [(0, 0, {
                'product_id': self.env.ref('product.product_product_12').id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })
                           ],
        })

    def test_alternate_shipping_address_computation(self):
        """Test alternate shipping address computation."""
        # Assign alternate address details
        self.sale_order.write({
            'alt_contact': 'John Doe',
            'alt_phone': '123456789',
            'alt_building': 'Unit 10',
            'alt_street': '123 Test Street',
            'alt_street2': 'Suite 5',
            'alt_zip': '1010',
            'alt_city': 'Test City',
            'alt_state_id': self.state.id,
            'alt_country_id': self.country.id,
        })
        self.sale_order._compute_alternate_shipping_address()
        expected_address = (
            "ATT:John Doe\n"
            "Unit 10\n"
            "123 Test Street\n"
            "Suite 5\n"
            "Test City 1010\n"
            "Auckland\n"
            "Test123\n"
            "ph:123456789"
        )
        self.assertEqual(
            self.sale_order.alternate_shipping_address,
            expected_address,
            "The alternate shipping address is not computed correctly."
        )

    def test_no_alternate_shipping_address(self):
        """Test alternate shipping address computation when no address fields are provided."""
        # Clear all alternate address fields
        self.sale_order.write({
            'alt_contact': '',
            'alt_phone': '',
            'alt_building': '',
            'alt_street': '',
            'alt_street2': '',
            'alt_zip': '',
            'alt_city': '',
            'alt_state_id': False,
            'alt_country_id': False,
        })
        self.sale_order._compute_alternate_shipping_address()
        self.assertFalse(
            self.sale_order.alternate_shipping_address,
            "Alternate shipping address should be empty when no fields are set."
        )
