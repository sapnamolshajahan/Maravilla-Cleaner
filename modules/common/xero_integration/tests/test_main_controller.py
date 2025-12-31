import base64
import json
from unittest.mock import patch
from odoo.tests.common import HttpCase, tagged


@tagged('common', 'xero_integration')
class TestXeroConnector(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company',
            'xero_access_token_url': 'https://identity.xero.com/connect/token',
            'xero_client_id': '90A3791BF8944D68AD0D64ECC682DD9F',
            'xero_client_secret': 'tUbRjW-i2HJuulw6-63VDO7CwmJJKPv-DEql9w4WXn5VrAfF',
            'xero_redirect_url': 'https://mock.redirect.url',
            'xero_tenant_id_url': 'https://mock.api.xero.com/connections',
        })
        cls.env.company = cls.company

    @patch('requests.post')
    @patch('requests.request')
    def test_get_auth_code(self, mock_request, mock_post):
        # Mock the POST request to fetch access token
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = json.dumps({
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token'
        })

        # Mock the GET request to fetch tenant details
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps([
            {'tenantId': 'mock_tenant_id', 'tenantName': 'Mock Tenant Name'}
        ])

        # Simulate GET request with authorization code
        response = self.url_open(f"{self.base_url()}/get_auth_code?code=mock_auth_code")

        # Check if the request was successful
        self.assertIn("Authenticated Successfully", response.text)
