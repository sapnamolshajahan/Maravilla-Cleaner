# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("common", "purchase_alternate_shipping_address")
class TestPurchaseOrder(TransactionCase):
    def setUp(self):
        super(TestPurchaseOrder, self).setUp()
        self.country = self.env['res.country'].create({'name': 'Test Country', 'code': 'TEST C'})
        self.state = self.env['res.country.state'].create({
            'name': 'Test State',
            'code': 'TSTC',
            'country_id': self.country.id
        })

        self.partner_id = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'TST CSTMR <test@test.example.com>'
        })

        self.purchase_order = self.env['purchase.order'].create({
            'name': 'Test PO',
            'partner_id': self.partner_id.id,
            'alt_contact': 'John Doe',
            'alt_phone': '1234567890',
            'alt_building': 'Building 1',
            'alt_street': '123 Test St',
            'alt_street2': 'Suite 4B',
            'alt_zip': '56789',
            'alt_city': 'Test City',
            'alt_state_id': self.state.id,
            'alt_country_id': self.country.id,
        })


    def test_make_alt_addr_from_fields(self):
        """Test alternate address generation."""
        expected_address = (
            "ATT:John Doe\n"
            "Building 1\n"
            "123 Test St\n"
            "Suite 4B\n"
            "Test City 56789\n"
            "Test State\n"
            "Test Country\n"
            "ph:1234567890"
        )
        self.assertEqual(self.purchase_order._make_alt_addr_from_fields(), expected_address)

    def test_compute_alternate_delivery_address(self):
        """Test computation of alternate delivery address."""
        self.purchase_order._compute_alternate_delivery_address()
        expected_address = (
            "ATT:John Doe\n"
            "Building 1\n"
            "123 Test St\n"
            "Suite 4B\n"
            "Test City 56789\n"
            "Test State\n"
            "Test Country\n"
            "ph:1234567890"
        )
        self.assertEqual(self.purchase_order.alternate_shipping_address, expected_address)

    def test_is_alt_address_separate_fields(self):
        """Test computation of is_alt_address_separate_fields."""
        self.purchase_order._compute_is_alt_address_separate_fields()
        self.assertTrue(self.purchase_order.is_alt_address_separate_fields)

        self.purchase_order.write({
            'alt_street': False,
            'alt_street2': False,
        })
        self.purchase_order._compute_is_alt_address_separate_fields()
        self.assertFalse(self.purchase_order.is_alt_address_separate_fields)