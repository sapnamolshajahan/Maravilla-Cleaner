from unittest.mock import patch, MagicMock
from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError


@tagged('common', 'xero_integration')
class TestXeroToken(TransactionCase):

    def setUp(self):
        super(TestXeroToken, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'xero_client_id': '90A3791BF8944D68AD0D64ECC682DD9F',
            'xero_client_secret': 'tUbRjW-i2HJuulw6-63VDO7CwmJJKPv-DEql9w4WXn5VrAfF',
            'xero_tenant_id': 'test_tenant_id',
            'xero_oauth_token': 'test_oauth_token',
            'refresh_token_xero': 'test_refresh_token'
        })

        self.xero_token = self.env['xero.token'].create({
            'company_id': self.company.id,
            'refresh_token_xero': 'test_refresh_token',
            'access_token': 'test_access_token',
        })

    @patch('requests.post')
    def test_refresh_token(self, mock_post):
        # Mock response for the token refresh API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'refresh_token': 'new_refresh_token',
            'access_token': 'new_access_token',
        }
        mock_post.return_value = mock_response

        # Call the method
        self.xero_token.refresh_token()

        # Check if the token was updated
        self.xero_token.refresh()
        self.assertEqual(self.xero_token.refresh_token_xero, 'new_refresh_token')
        self.assertEqual(self.xero_token.access_token, 'new_access_token')

    def test_get_head(self):
        headers = self.xero_token.get_head()

        # Check the headers
        self.assertEqual(headers['Authorization'], f"Bearer {self.company.xero_oauth_token}")
        self.assertEqual(headers['Xero-tenant-id'], self.company.xero_tenant_id)
        self.assertEqual(headers['Accept'], 'application/json')

    @patch('requests.post')
    def test_refresh_token_failure(self, mock_post):
        # Mock response for failed token refresh
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'invalid_grant'}
        mock_post.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.xero_token.refresh_token()
