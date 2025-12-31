# -*- coding: utf-8 -*-
import logging

from io import BytesIO
from odoo.tests import common, tagged
import base64

_logger = logging.getLogger(__name__)

@tagged("common", "product_listprice_import")
class TestProductListPriceImport(common.TransactionCase):
    """Class to test operation related product.product import csv workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.product_1 = self.env['product.product'].create({
            "name": "Test Product 1",
            "default_code": "TEST01",
            "list_price": 10.0,
        })
        self.product_2 = self.env['product.product'].create({
            "name": "Test Product 2",
            "default_code": "TEST02",
            "list_price": 20.0,
        })

    def _create_test_excel_file(self):
        """ Helper to create a test Excel file in memory """
        csv_content = (
            "Product-Code,List-Price\n"
            "TEST01,15.50\n"
            "TEST02,25.00\n"
            "INVALID01,30.00\n"
            "TEST01,abc\n"
            "TEST02,\n"
        )
        return BytesIO(csv_content.encode("utf-8"))

    def test_import_csv_success(self):
        """Test successful import of sale order lines from a valid CSV."""
        excel_file = self._create_test_excel_file()
        encoded_file = base64.b64encode(excel_file.getvalue())
        wizard = self.env["product.listprice.import"].create({
            "file": encoded_file,
        })
        wizard.button_import()
        self.assertEqual(self.product_1.list_price, 15.50, "List price for TEST01 should be updated to 15.50")
        self.assertEqual(self.product_2.list_price, 25.00, "List price for TEST02 should be updated to 25.00")
        expected_errors = [
            "Line 4 - Unable to find product=INVALID01",
            "Line 5 - non-numeric price: abc",
            "Line 6 - empty price field",
        ]
        for error in expected_errors:
            self.assertIn(error, wizard.notes, f"Expected error not found in notes: {error}")
        # Verify the process and error counts in notes
        self.assertIn("Processed: 2", wizard.notes, "Incorrect processed count in notes")
        self.assertIn("Errors: 3", wizard.notes, "Incorrect error count in notes")
