from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch

@tagged('common', 'xero_integration')
class TestProductProduct(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TEST123',
            'standard_price': 10.0,
            'list_price': 20.0,
            'description_sale': '<p>Sale Description</p>',
            'description_purchase': '<p>Purchase Description</p>',
            'company_id': self.company.id,
        })
        self.xero_config = self.env['res.company'].create({
            'name': 'Xero Company',
            'xero_oauth_token': 'valid_token'
        })

    @patch('requests.request')
    def test_create_product_in_xero(self, mock_request):
        """Test product creation in Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = '{"Items":[{"ItemID":"XERO123"}]}'

        # Call method to create product in Xero
        self.product.create_product_in_xero()

        # Check if Xero product ID is set correctly
        self.assertEqual(self.product.xero_product_id, 'XERO123')

    @patch('requests.request')
    def test_create_product_in_xero_failure(self, mock_request):
        """Test product creation failure in Xero"""
        mock_request.return_value.status_code = 400
        mock_request.return_value.text = '{"Message":"Bad Request"}'

        # Call method to create product in Xero and check for ValidationError
        with self.assertRaises(ValidationError):
            self.product.create_product_in_xero()

    def test_remove_html_tags(self):
        """Test removing HTML tags from product description"""
        cleaned_description = self.product.remove_html_tags('<p>Test Description</p>')
        self.assertEqual(cleaned_description, 'Test Description')

    def test_prepare_product_export_dict(self):
        """Test preparing the product export dictionary"""
        export_dict = self.product.prepare_product_export_dict()
        self.assertIn("Code", export_dict)
        self.assertIn("Name", export_dict)
        self.assertIn("Description", export_dict)
        self.assertEqual(export_dict["Name"], 'Test Product')
        self.assertEqual(export_dict["Code"], 'TEST123')

    @patch('requests.request')
    def test_create_single_product_in_xero(self, mock_request):
        """Test creating a single product in Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = '{"Items":[{"ItemID":"XERO123"}]}'

        # Call method to create single product in Xero
        self.product.create_single_product_in_xero(self.product)

        # Check if Xero product ID is set correctly
        self.assertEqual(self.product.xero_product_id, 'XERO123')
