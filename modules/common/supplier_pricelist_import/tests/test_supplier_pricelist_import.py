# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
import base64

@tagged("common","supplier_pricelist_import")
class TestSupplierPricelistImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({'name': 'Test Supplier'})
        self.company = self.env.company
        self.currency = self.company.currency_id
        self.product = self.env['product.product'].create({'name': 'Test Product', 'default_code': 'ABC01'})
        self.supplier_pricelist_import = self.env['supplier.pricelist.import'].create({
            'supplier': self.supplier.id,
            'currency': self.currency.id,
            'file': base64.b64encode(b'Product-Code,Unit-Price,Min-QTY,Vendor-Code,Lead-Time,Is Preferred Supplier\n"ABC01",10.5,50,"XYABC-484",5,Yes')
        })

    def test_import_valid_data(self):
        self.supplier_pricelist_import.button_import()
        supplier_info = self.env['product.supplierinfo'].search([('partner_id', '=', self.supplier.id)])
        self.assertEqual(len(supplier_info), 1, "Supplier info should be created")
        self.assertEqual(supplier_info.price, 10.5, "Unit price should be updated correctly")

    def test_import_invalid_product(self):
        self.supplier_pricelist_import.file = base64.b64encode(b'Product-Code,Unit-Price\n"INVALID",10.5')
        self.supplier_pricelist_import.button_import()
        self.assertIn("Unable to find product", self.supplier_pricelist_import.notes, "Error should be logged for invalid product")

    def test_import_invalid_price(self):
        self.supplier_pricelist_import.file = base64.b64encode(b'Product-Code,Unit-Price\n"ABC01","INVALID"')
        self.supplier_pricelist_import.button_import()
        self.assertIn("non-numeric quantity", self.supplier_pricelist_import.notes, "Error should be logged for invalid price")

    def test_import_no_price(self):
        self.supplier_pricelist_import.file = base64.b64encode(b'Product-Code,Unit-Price\n"ABC01",')
        self.supplier_pricelist_import.button_import()
        self.assertIn("empty price field", self.supplier_pricelist_import.notes, "Error should be logged for empty price")

    def test_import_multiple_products(self):
        self.env['product.product'].create({'name': 'Duplicate Product', 'default_code': 'ABC01'})
        with self.assertRaises(UserError):
            self.supplier_pricelist_import.button_import()

