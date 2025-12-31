from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import json


@tagged('common', 'xero_integration')
class TestCustomer(TransactionCase):

    def setUp(self):
        super(TestCustomer, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'xero_oauth_token': 'valid_token',  # Assuming token is required
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
            'street': '123 Test St',
            'city': 'Test City',
            'zip': '12345',
            'country_id': self.env.ref('base.us').id,
        })

    def test_get_xero_partner_ref(self):
        # Simulate that the partner already has an xero_cust_id
        self.partner.xero_cust_id = '12345'

        ref = self.partner.get_xero_partner_ref(self.partner)

        # Assertions
        self.assertEqual(ref, '12345')

    def test_prepare_address(self):
        # Prepare address for a partner
        address = self.partner
        address_dict = self.partner.prepare_address('STREET', address)

        # Assertions
        self.assertIn('AddressType', address_dict)
        self.assertEqual(address_dict['AddressType'], 'STREET')
        self.assertIn('AddressLine1', address_dict)
        self.assertEqual(address_dict['AddressLine1'], '123 Test St')

    def test_prepare_from_partner(self):
        address_dict = self.partner.prepare_from_partner('STREET', '123 Test St', 'Apt 4', 'Test City', 'California', '12345', 'USA')

        # Assertions
        self.assertIn('AddressLine1', address_dict)
        self.assertEqual(address_dict['AddressLine1'], '123 Test St')

    def test_split_name(self):
        fname, lname = self.partner.split_name('John Doe')

        # Assertions
        self.assertEqual(fname, 'John')
        self.assertEqual(lname, 'Doe')

    @patch('requests.request')
    def test_prepare_customer_export_dict(self, mock_request):
        # Mocking the Xero API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'Contacts': [{
                'ContactID': '123456',
            }]
        })
        mock_request.return_value = mock_response

        export_dict = self.partner.prepare_customer_export_dict()

    @patch('requests.request')
    def test_create_customer_in_xero(self, mock_request):
        # Mocking the Xero API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'Contacts': [{
                'ContactID': '123456',
            }]
        })
        mock_request.return_value = mock_response

        # Call the method to create customer in Xero
        self.partner.create_customer_in_xero()

        # Assertions
        self.assertEqual(self.partner.xero_cust_id, '123456')

    @patch('requests.request')
    def test_create_main_customer_in_xero(self, mock_request):
        # Mocking the Xero API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'Contacts': [{
                'ContactID': '123456',
            }]
        })
        mock_request.return_value = mock_response

        # Call the method to create customer in Xero
        self.partner.create_main_customer_in_xero(self.partner, self.company)

        # Assertions
        self.assertEqual(self.partner.xero_cust_id, '123456')

    @patch('requests.request')
    def test_create_customer_in_xero_401_error(self, mock_request):
        # Mocking a 401 error response from Xero
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_request.return_value = mock_response

        # Call the method to attempt customer export
        with self.assertRaises(ValidationError):
            self.partner.create_customer_in_xero()

    @patch('requests.request')
    def test_create_main_customer_in_xero_400_error(self, mock_request):
        # Mocking a 400 error response from Xero
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = json.dumps({
            'Elements': [{
                'ValidationErrors': [{'Message': 'Invalid data'}]
            }]
        })
        mock_request.return_value = mock_response

        # Call the method to attempt customer export
        with self.assertRaises(ValidationError):
            self.partner.create_main_customer_in_xero(self.partner, self.company)

    @patch('requests.request')
    def test_create_customer_in_xero_failure(self, mock_request):
        # Mocking a generic failure response from Xero
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_request.return_value = mock_response

        # Call the method to attempt customer export
        self.partner.create_customer_in_xero()

        # Assertions
        self.assertEqual(self.partner.xero_cust_id, False)
