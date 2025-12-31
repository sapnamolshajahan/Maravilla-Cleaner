# -*- coding: utf-8 -*-
import re
import logging

from odoo import http
from odoo.http import request
from odoo.tools import config

from werkzeug.exceptions import Unauthorized

from odoo.addons.rest_api.models.common import valid_response, invalid_response
from .variables import LOGIN_ROUTE, HEADER_ODOO_AUTHORISATION

_logger = logging.getLogger(__name__)

expires_in = "rest_api.access_token_expires_in"


db_filter_api = http.db_filter


def db_filter(dbs, httprequest=None):
    dbs = db_filter_api(dbs, httprequest)
    httprequest = httprequest or http.request.httprequest

    db_filter_hdr = httprequest.environ.get('HTTP_DATABASE')

    if db_filter_hdr:
        dbs = [db for db in dbs if re.match(db_filter_hdr, db)]

    return dbs


if config.get('proxy_mode') and config.get('db_filter_api'):
    _logger.info('Allowing to set db_filter via API')
    http.db_filter = db_filter


class AccessToken(http.Controller):
    def __init__(self):
        self._token = request.env["api.access_token"]
        self._expires_in = request.env.ref(expires_in).sudo().value

    @http.route(LOGIN_ROUTE, methods=['GET', 'OPTIONS'], type="http", auth="none", csrf=False, cors="*")
    def token(self):
        """The token URL to be used for getting the access_token:

        :param: **kwargs must contain login and password.

        :returns status code 404 if failed error message in the body in json format
                 status code 202 if successful with the access_token.

        Example:
           import requests

           headers = {
                HEADER_ODOO_AUTHORISATION: <token> (generated in Odoo)
            }


           base_url = 'http://odoo.com'
           example = requests.get('{}/api/v1/login'.format(base_url), data=data, headers=headers)
           content = json.loads(example.content.decode('utf-8'))
           headers.update(access-token=content.get('access_token'))

        """
        headers = request.httprequest.headers
        odoo_token = headers.get(HEADER_ODOO_AUTHORISATION)

        if not odoo_token:
            logging.warning("Attempt to access the API without auth token")
            return invalid_response(
                error_type="Unauthorised",
                message="You're not allowed to access this API"
            )

        # Find user by token
        try:
            user = request.env['res.users'].get_user_by_auth_token(token=odoo_token)

        except Unauthorized:
            logging.warning("Attempt to access the API with incorrect auth token {}".format(odoo_token))
            return invalid_response(
                error_type="Unauthorised",
                message="Token is invalid"
            )

        # User is found
        uid = user.id

        # Set db from params
        if headers.get('database'):
            request.session['db'] = headers['database']

        # Generate access token or get existing ones (if there are any active)
        tokens, company_id = request.env['api.access_token'].find_one_or_create_token(user_id=uid, create=True)

        if not tokens:
            return invalid_response(
                error_type="Unauthorised",
                message="Token is invalid"
            )

        # Successful response:
        logging.info("API Token authorised with access token = {}".format(tokens[0]))
        return valid_response({
            "uid": uid,
            "company": company_id,
            "access_token": tokens[0],
            "expires_in": self._expires_in,
        })
