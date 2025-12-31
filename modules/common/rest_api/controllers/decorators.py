# -*- coding: utf-8 -*-
import logging
import functools

from odoo.http import request
from odoo.addons.rest_api.models.common import invalid_response, options_response

_logger = logging.getLogger(__name__)


ACCESS_TOKEN = 'Access-Token'


def validate_token(func):

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get(ACCESS_TOKEN)

        if request.httprequest.method == 'OPTIONS':
            _logger.info("API preflight request has been made".format(access_token))
            return options_response()

        _logger.info("API accessed with token {}".format(access_token))
        if not access_token:
            error_type = "access_token_not_found"
            message = "access"

            return invalid_response(error_type, message, 401)

        existing_token = request.env["api.access_token"].sudo().search([
            ("token", "=", access_token),
        ], order="id DESC", limit=1)

        existing_tokens, _ = existing_token.find_one_or_create_token(user_id=existing_token.user.id)
        if access_token not in existing_tokens:
            error_type = "access_token_invalid"
            message = "Access token not found or expired"
            _logger.warning("API not authorised with token {}".format(access_token))

            return invalid_response(error_type, message, 401)

        # Keep some values in the session
        request.session['user'] = existing_token.user.id
        request.session['company'] = existing_token.company.id
        request.session['tz'] = existing_token.user.partner_id.tz

        return func(self, *args, **kwargs)

    return wrap


def validate_model_allowed(func):

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        model = request.env[self._model].sudo().search([("model", "=", kwargs.get('model'))], limit=1)

        if not model:
            error_type = "invalid_object_model"
            message = "The model {model} is not available in the registry.".format(model=model.model)
            return invalid_response(error_type, message, 404)

        if not model.allow_rest_api:
            error_type = "model_not_allowed"
            message = "Model {model} is not available in the API".format(model=model.model)
            return invalid_response(error_type, message, 403)

        return func(self, *args, **kwargs)

    return wrap


def validate_record_id(func):

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        record_id = kwargs.get('record_id')

        # Set record ID to the response
        if not record_id:
            error_type = "No Record ID"
            message = "Record ID must be provided for this endpoint."
            return invalid_response(error_type, message, 404)

        try:
            int(record_id)

        except ValueError:
            error_type = "Record ID is invalid"
            message = "Record ID must be provided for this endpoint."
            return invalid_response(error_type, message, 403)

        return func(self, *args, **kwargs)

    return wrap
