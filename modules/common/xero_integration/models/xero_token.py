import logging

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import base64
import requests
import json

_logger = logging.getLogger(__name__)


class XeroToken(models.Model):
    _name = 'xero.token'
    _description = 'Xero Token'

    refresh_token_xero = fields.Char('Refresh Token')
    access_token = fields.Char('Access Token')
    xero_oauth_token = fields.Char('Oauth Token', help="OAuth Token")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def get_head(self):
        xero_config = self.env.company
        client_id = xero_config.xero_client_id
        client_secret = xero_config.xero_client_secret

        data = client_id + ":" + client_secret
        encodedBytes = base64.b64encode(data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")
        headers = {
            'Authorization': "Bearer " + str(xero_config.xero_oauth_token),
            'Xero-tenant-id': xero_config.xero_tenant_id,
            'Accept': 'application/json'

        }
        return headers

    def refresh_token(self):

        xero_id = self.env.company

        client_id = xero_id.xero_client_id
        client_secret = xero_id.xero_client_secret
        url = 'https://identity.xero.com/connect/token'
        data = client_id + ":" + client_secret

        encodedBytes = base64.b64encode(data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")

        headers = {
            'Authorization': "Basic " + encodedStr,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data_token = {
            'grant_type': 'refresh_token',
            'refresh_token': xero_id.refresh_token_xero,
        }
        access_token = requests.post(url, data=data_token, headers=headers)
        parsed_token_response = json.loads(access_token.text)

        if parsed_token_response and access_token.status_code == 200:
            existing = self.search([('company_id', '=', self.env.company.id)])
            if existing:
                existing.write({'refresh_token_xero': parsed_token_response.get('refresh_token'),
                                'xero_oauth_token': parsed_token_response.get('access_token'),
                                'access_token': parsed_token_response.get('access_token')})
            else:
                self.create({'refresh_token_xero': parsed_token_response.get('refresh_token'),
                             'access_token': parsed_token_response.get('access_token'),
                             'xero_oauth_token': parsed_token_response.get('access_token'),
                             'company_id': self.env.company.id})

        if access_token.status_code == 200:
            _logger.info(_("(UPDATE) - Token generated successfully"))

        elif access_token.status_code == 401:
            _logger.info(_("Time Out.\nPlease Check Your Connection or error in application or refresh token..!!"))
        elif access_token.status_code == 400:
            if parsed_token_response.get('error'):
                raise ValidationError(parsed_token_response.get('error'))
