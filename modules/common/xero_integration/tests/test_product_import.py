from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch
import json

@tagged('common', 'xero_integration')
class TestResCompany(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.res_company = self.env['res.company'].create({
            'name': 'Test Company',
            'xero_oauth_token': 'valid_token',
        })
        self.product_data = {
            'ItemID': 'XERO123',
            'Code': 'TEST001',
            'Name': 'Test Product',
            'SalesDetails': {
                'UnitPrice': 100.0,
                'TaxType': 'TAX1',
                'AccountCode': '400',
            },
            'PurchaseDetails': {
                'UnitPrice': 80.0,
                'TaxType': 'TAX2',
                'AccountCode': '500',
            },
            'IsTrackedAsInventory': True,
            'IsPurchased': True,
            'IsSold': True,
            'Description': 'Test product description',
            'PurchaseDescription': 'Test purchase description'
        }
        self.product = self.env['product.product'].create({
            'name': 'Existing Product',
            'default_code': 'EXIST001',
            'xero_product_id': 'XERO123',
            'company_id': self.company.id
        })

    @patch('requests.request')
    def test_import_products(self, mock_request):
        """Test importing products from Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'Items': [self.product_data]})

        # Call method to import products
        res = self.res_company.import_products()

        # Check that product is created in Odoo
        imported_product = self.env['product.product'].search([('xero_product_id', '=', 'XERO123')])
        self.assertEqual(imported_product.name, 'Test Product')
        self.assertEqual(imported_product.default_code, 'TEST001')

    @patch('requests.request')
    def test_import_products_no_data(self, mock_request):
        """Test handling of no products in Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'Items': []})

        # Call method to import products and check for ValidationError
        with self.assertRaises(ValidationError):
            self.res_company.import_products()

    @patch('requests.request')
    def test_create_products(self, mock_request):
        """Test creating products from Xero data"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'Items': [self.product_data]})

        # Create products from the mocked Xero data
        self.res_company.create_products(mock_request.return_value)

        # Verify product creation in Odoo
        product = self.env['product.product'].search([('xero_product_id', '=', 'XERO123')])
        self.assertTrue(product)
        self.assertEqual(product.name, 'Test Product')

    @patch('requests.request')
    def test_create_imported_products(self, mock_request):
        """Test creating/updating products with the provided data"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'Items': [self.product_data]})

        # Call method to create or update imported products
        self.res_company.create_imported_products(self.product_data)

        # Check if the product is updated or created in Odoo
        product = self.env['product.product'].search([('xero_product_id', '=', 'XERO123')])
        self.assertTrue(product)
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.default_code, 'TEST001')
        self.assertEqual(product.list_price, 100.0)
        self.assertEqual(product.standard_price, 80.0)

    @patch('requests.request')
    def test_fetch_the_required_product(self, mock_request):
        """Test fetching and creating a required product from Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'Items': [self.product_data]})

        # Call method to fetch required product
        self.res_company.fetch_the_required_product('TEST001')

        # Check that the product was created or updated
        product = self.env['product.product'].search([('default_code', '=', 'TEST001')])
        self.assertTrue(product)
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.default_code, 'TEST001')

    def test_create_imported_products_existing(self):
        """Test updating an existing product"""
        updated_data = self.product_data.copy()
        updated_data['Name'] = 'Updated Product'

        # Call method to update existing product
        self.res_company.create_imported_products(updated_data)

        # Verify the product name is updated
        product = self.env['product.product'].search([('xero_product_id', '=', 'XERO123')])
        self.assertEqual(product.name, 'Updated Product')
