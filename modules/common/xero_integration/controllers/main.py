import base64

import requests
import json
import logging
from odoo import http, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class XeroConnector(http.Controller):

    @http.route('/get_auth_code', type="http", auth="public", website=True)
    def get_auth_code(self, **kwarg):
        _logger.info("get_auth_code - called")
        if kwarg.get('code'):
            _logger.info(f"get_auth_code - code: {kwarg.get('code')}")
            access_token_url = http.request.env.company.xero_access_token_url

            xero_id = http.request.env["res.company"].search([("id", "=", http.request.env.company.id)], limit=1).sudo()
            xero_token = http.request.env["xero.token"].search([("id", "=", http.request.env.company.id)], limit=1).sudo()
            client_id = xero_id.xero_client_id
            client_secret = xero_id.xero_client_secret
            redirect_uri = xero_id.xero_redirect_url

            data = client_id + ":" + client_secret
            encodedBytes = base64.b64encode(data.encode("utf-8"))
            encodedStr = str(encodedBytes, "utf-8")
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': "Basic " + encodedStr
            }
            data_token = {
                'code': kwarg.get('code'),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            _logger.info(f"get_auth_code - post url: {access_token_url}, data: {data_token}")
            access_token = requests.post(access_token_url, data=data_token, headers=headers, verify=False)
            _logger.info(f"get_auth_code - post response: {access_token.status_code}")
      
            if not access_token:
                raise ValidationError('No access token')
            if access_token:
                parsed_token_response = json.loads(access_token.text)

                if parsed_token_response and xero_id:
                    xero_id.write({
                        'xero_oauth_token': parsed_token_response.get('access_token'),
                        'refresh_token_xero': parsed_token_response.get('refresh_token'),
                    })
                if parsed_token_response and xero_token:
                    xero_token.write({
                        'xero_oauth_token': parsed_token_response.get('access_token'),
                        'access_token': parsed_token_response.get('access_token'),
                        'refresh_token_xero': parsed_token_response.get('refresh_token'),
                    })

                header1 = {
                    'Authorization': "Bearer " + xero_id.xero_oauth_token,
                    'Content-Type': 'application/json'
                        }
                xero_tenant_id_url = http.request.env.company.xero_tenant_id_url
                _logger.info(f"get_auth_code - get url: {xero_tenant_id_url}")
                xero_tenant_response=requests.request('GET', xero_tenant_id_url, headers=header1)
                _logger.info(f"get_auth_code - get status_code: {xero_tenant_response.status_code}")

                parsed_tenent = json.loads(xero_tenant_response.text)

                if parsed_tenent:
                    for tenant in parsed_tenent:
                        if 'tenantId' in tenant:
                            xero_id.xero_tenant_id = tenant.get('tenantId')
                            xero_id.xero_tenant_name = tenant.get('tenantName')
                    _logger.info(_("Authorization successfully!"))

                    country_name = xero_id.import_country()

                    xero_id.write({
                        'xero_country_name': country_name
                    })
                else:
                    _logger.info(_("Bugger!"))
                    raise ValidationError('No access token')

        return "Authenticated Successfully..!! \n You can close this window now"


