from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError


@tagged('common', 'xero_integration')
class TestXeroIntegration(TransactionCase):

    def setUp(self):
        super(TestXeroIntegration, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'xero_client_id': '90A3791BF8944D68AD0D64ECC682DD9F',
            'xero_client_secret': 'tUbRjW-i2HJuulw6-63VDO7CwmJJKPv-DEql9w4WXn5VrAfF',
            'xero_redirect_url': 'https://test.redirect.url',
        })
        self.xero_import_type = self.env['xero.import.type'].create({
            'name': 'Test Import Type',
            'date_from_visible': True,
            'function_name': 'mock_import_function',
        })
        self.xero_import = self.env['xero.import'].create({
            'xero_import_type': self.xero_import_type.id,
            'date_from': '2025-01-01',
        })
        self.xero_authenticate = self.env['xero.authenticate'].create({
            'name': 'Test Authentication',
        })
        self.xero_refresh_token = self.env['xero.refresh.token'].create({
            'name': 'Test Refresh Token',
        })

    def test_run_import(self, mock_import_function):
        """Test that the `run_import` method calls the correct function."""
        mock_import_function.return_value = None
        self.xero_import.run_import()
        mock_import_function.assert_called_once()

    def test_run_import_error(self):
        """Test that `run_import` raises an error if the function is invalid."""
        self.xero_import_type.function_name = 'non_existent_function'
        with self.assertRaises(UserError):
            self.xero_import.run_import()

    def test_run_authenticate_url_generation(self):
        """Test that `run_authenticate` generates the correct URL."""
        result = self.xero_authenticate.run_authenticate()
        self.assertIn('https://login.xero.com/identity/connect/authorize', result['url'])
        self.assertIn('response_type=code', result['url'])
        self.assertIn('client_id=90A3791BF8944D68AD0D64ECC682DD9F', result['url'])
        self.assertIn('redirect_uri=https://test.redirect.url', result['url'])

    def test_run_authenticate_missing_client_id(self):
        """Test that `run_authenticate` raises an error if the client ID is missing."""
        self.company.xero_client_id = False
        with self.assertRaises(ValidationError):
            self.xero_authenticate.run_authenticate()

    def test_run_authenticate_missing_client_secret(self):
        """Test that `run_authenticate` raises an error if the client secret is missing."""
        self.company.xero_client_secret = False
        with self.assertRaises(ValidationError):
            self.xero_authenticate.run_authenticate()

    def test_run_token_refresh(self, mock_refresh_token):
        """Test that `run_token_refresh` calls the token refresh method."""
        mock_refresh_token.return_value = None
        self.xero_refresh_token.run_token_refresh()
        mock_refresh_token.assert_called_once()
