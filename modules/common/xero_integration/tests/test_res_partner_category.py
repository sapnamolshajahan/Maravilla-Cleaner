from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch, MagicMock
import json


@tagged('common', 'xero_integration')
class TestContactGroup(TransactionCase):

    def setUp(self):
        super(TestContactGroup, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'xero_oauth_token': 'valid_token',  # Assuming token is required
        })
        self.contact_group = self.env['res.partner.category'].create({
            'name': 'Test Contact Group',
            'active': True,
        })

    def test_prepare_contact_group_export_dict(self):
        # Prepare the export dict for a contact group
        export_dict = self.contact_group.prepare_contact_group_export_dict()

        # Assertions
        self.assertIn('Status', export_dict)
        self.assertEqual(export_dict['Status'], 'ACTIVE')
        self.assertIn('Name', export_dict)
        self.assertEqual(export_dict['Name'], 'Test Contact Group')

    @patch('requests.request')
    def test_create_contact_group_in_xero_create(self, mock_request):
        # Mocking the Xero API response for creating a contact group
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'ContactGroups': [{
                'ContactGroupID': '123456',
            }]
        })
        mock_request.return_value = mock_response

        # Call the method to create the contact group in Xero
        self.contact_group.create_contact_group_in_xero()

        # Assertions
        self.assertEqual(self.contact_group.xero_contact_group_id, '123456')

    @patch('requests.request')
    def test_create_contact_group_in_xero_update(self, mock_request):
        # Mocking the Xero API response for updating a contact group
        self.contact_group.xero_contact_group_id = '123456'  # Assuming the contact group already has an ID
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = json.dumps({
            'ContactGroups': [{
                'ContactGroupID': '123456',
            }]
        })
        mock_request.return_value = mock_response

        # Call the method to update the contact group in Xero
        self.contact_group.create_contact_group_in_xero()

        # Assertions
        self.assertEqual(self.contact_group.xero_contact_group_id, '123456')

    @patch('requests.request')
    def test_create_contact_group_in_xero_401_error(self, mock_request):
        # Mocking a 401 error response from Xero
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_request.return_value = mock_response

        # Call the method to attempt contact group export
        with self.assertRaises(ValidationError):
            self.contact_group.create_contact_group_in_xero()

    @patch('requests.request')
    def test_create_contact_group_in_xero_failure(self, mock_request):
        # Mocking a failure response from Xero
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_request.return_value = mock_response

        # Call the method to attempt contact group export
        self.contact_group.create_contact_group_in_xero()

        # Assertions
        self.assertEqual(self.contact_group.xero_contact_group_id, False)
