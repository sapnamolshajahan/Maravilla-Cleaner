from odoo.tests.common import tagged, TransactionCase
from unittest.mock import patch, MagicMock
import json


@tagged('common', 'xero_integration')
class TestResCompany(TransactionCase):

    def setUp(self):
        super(TestResCompany, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })

    @patch('requests.request')
    def test_import_customers(self, mock_request):
        # Mocking the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'Contacts': [{
                'ContactID': '123',
                'Name': 'Test Customer',
                'EmailAddress': 'test@example.com',
                'AccountNumber': 'ACC123',
                'PaymentTerms': {
                    'Sales': {'Type': 'DAYSAFTERBILLDATE', 'Day': 30},
                    'Bills': {'Type': 'DAYSAFTERBILLMONTH', 'Day': 60},
                },
                'Addresses': [{
                    'AddressType': 'POBOX',
                    'AddressLine1': '123 Test Street',
                    'City': 'Test City',
                    'PostalCode': '12345',
                    'Country': 'US',
                }],
                'Phones': [{'PhoneType': 'DEFAULT', 'PhoneNumber': '1234567890'}],
            }]
        })
        mock_request.return_value = mock_response

        # Trigger the import customers functionality
        self.company.import_customers()

        # Assertions
        customer = self.env['res.partner'].search([('xero_cust_id', '=', '123')])
        self.assertTrue(customer, "Customer was not created")
        self.assertEqual(customer.name, 'Test Customer')
        self.assertEqual(customer.email, 'test@example.com')
        self.assertEqual(customer.ref, 'ACC123')

    @patch('requests.request')
    def test_create_contact(self, mock_request):
        # Mocking the API response
        parent_partner = self.env['res.partner'].create({'name': 'Parent Partner'})
        contact_data = [{'FirstName': 'John', 'LastName': 'Doe', 'EmailAddress': 'john.doe@example.com'}]

        self.company.create_contact(parent_partner.id, '123', contact_data)

        # Assertions
        contact = self.env['res.partner'].search([('email', '=', 'john.doe@example.com')])
        self.assertTrue(contact, "Contact was not created")
        self.assertEqual(contact.parent_id.id, parent_partner.id)
        self.assertEqual(contact.name, 'John Doe')

    def test_calc_payment_terms(self):
        payment_terms = self.company.calc_payment_terms('DAYSAFTERBILLDATE', 30)
        self.assertTrue(payment_terms, "Payment terms were not created")
        self.assertEqual(payment_terms.name, '30 day(s) after the bill date')

    @patch('requests.request')
    def test_import_contact_groups(self, mock_request):
        # Mocking the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'ContactGroups': [{
                'ContactGroupID': 'grp123',
                'Name': 'Test Group'
            }]
        })
        mock_request.return_value = mock_response

        # Trigger the import contact groups functionality
        self.company.import_contact_groups()

        # Assertions
        group = self.env['res.partner.category'].search([('xero_contact_group_id', '=', 'grp123')])
        self.assertTrue(group, "Contact group was not created")
        self.assertEqual(group.name, 'Test Group')

