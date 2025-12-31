from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError
import json

@tagged('common', 'rest_api')
class TestRestApi(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'password': 'testpassword'
        })
        self.token_model = self.env['rest.api.access.token']
        self.access_token = self.token_model.create({'user_id': self.user.id})

    def test_access_token_creation(self):
        """Test if access tokens are correctly created."""
        self.assertTrue(self.access_token.token, "Token should be generated")
        self.assertEqual(self.access_token.user_id, self.user, "Token should be linked to the correct user")

    def test_token_authentication(self):
        """Test if API authentication works with a valid token."""
        response = self.env['rest.api.controller'].authenticate(self.access_token.token)
        self.assertEqual(response['user_id'], self.user.id, "User ID should match the token owner")

    def test_invalid_token(self):
        """Test API authentication failure with an invalid token."""
        with self.assertRaises(AccessError):
            self.env['rest.api.controller'].authenticate('invalid_token')

    def test_user_access_restriction(self):
        """Test that unauthorized users cannot access protected API routes."""
        with self.assertRaises(AccessError):
            self.env['rest.api.access.token'].sudo(self.user).create({})

    def test_api_endpoint_response(self):
        """Test if API endpoints return expected responses."""
        response = self.env['rest.api.controller'].get('/api/test', headers={'Authorization': f'Bearer {self.access_token.token}'})
        self.assertEqual(response.status_code, 200, "API should return HTTP 200 OK")
