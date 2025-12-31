# -*- coding: utf-8 -*-
import logging
from odoo.tests import tagged, TransactionCase
from datetime import datetime
from odoo import fields

_logger = logging.getLogger(__name__)

@tagged('post_install', '-at_install')
class TestProductInventoryDownload(TransactionCase):
    """
    Test case for Product Inventory Download.
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()

        self.category = self.env["product.category"].create({"name": "Test Category"})
        self.supplier = self.env["res.partner"].create({"name": "Test Supplier", "supplier_rank": 1})
        self.location = self.env["stock.location"].create({"name": "Test Location", "usage": "internal"})
        self.product = self.env["product.product"].create({
            "name": "Test Product",
            "type": "consu",
            "categ_id": self.category.id,
            "standard_price": 10.0
        })

        self.inventory_report = self.env["product.inventory.download"].create({
            "as_at_date": fields.Date.today(),
            "product_category_ids": [(6, 0, [self.category.id])],
            "supplier_ids": [(6, 0, [self.supplier.id])],
            "include_location_ids": [(6, 0, [self.location.id])],
            "exclude_zero_quantity": True
        })



    def test_onchange_include_location_ids(self):
        """Test include_location_ids onchange method."""
        self.inventory_report.include_location_ids = self.location
        self.assertFalse(self.inventory_report.exclude_location_ids, "Exclude locations should be cleared")

    def test_onchange_exclude_location_ids(self):
        # Create the location if it does not exist
        test_location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal'
        })

        # Now, assign it to the `exclude_location_ids`
        self.inventory_report.exclude_location_ids = test_location
        self.inventory_report._onchange_exclude_location_ids()

        # Ensure that `include_location_ids` is cleared
        self.assertFalse(self.inventory_report.include_location_ids, "Include locations should be cleared")

    def test_get_stock_move_filter_date(self):
        """Test stock move filter date conversion."""
        self.env.context = dict(self.env.context, tz="Europe/London")  # ✅ Set a timezone
        report_date = self.inventory_report._get_stock_move_filter_date(fields.Date.today())
        self.assertIsInstance(report_date, str)

    def test_create_product_inventory_report(self):
        """Test the creation of the product inventory report."""
        result = self.inventory_report._create_product_inventory_report(
            [self.supplier.id],  # supplier_ids
            [self.category.id],  # category_ids
            [self.location.id],  # location_ids
            fields.Date.today(),  # as_at_date
            "test.xlsx",  # file_name
            [],  # exclude_location_ids
            True  # exclude_zero_quantity
        )
        self.assertTrue(isinstance(result, str), "Report generation should return a string message")

    def test_get_stock_locations(self):
        """Test retrieval of stock locations."""
        locations = self.inventory_report._get_stock_locations([self.location.id], [])
        self.assertIn(self.location, locations, "Returned locations should include the test location")

    def test_get_products(self):
        """Test retrieval of products."""
        products = self.inventory_report._get_products([self.supplier.id], [self.category.id])
        self.assertIn(self.product, products, "Returned products should include the test product")

    def test_get_inbound_quantities(self):
        """Test inbound quantity calculations."""
        inbound = self.inventory_report._get_inbound_quantities([self.location], [self.product], datetime.now(), 2)
        self.assertIsInstance(inbound, dict, "Inbound quantities should be returned as a dictionary")

    def test_get_outbound_quantities(self):
        """Test outbound quantity calculations."""
        outbound = self.inventory_report._get_outbound_quantities([self.location], [self.product], datetime.now(), 2)
        self.assertIsInstance(outbound, dict, "Outbound quantities should be returned as a dictionary")

