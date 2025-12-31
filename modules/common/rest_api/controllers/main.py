# -*- coding: utf-8 -*-
import logging
import json

from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

from odoo.addons.rest_api.models.common import (
    valid_response,
    json_valid_response,
    invalid_response,
    extract_arguments,
    prepare_payload,
    read_related_objects,
    improve_tuple_objects,
    include_computed_fields,
    get_post_return_data,
    format_datetime,
    replace_field_names,
    include_fixed_fields,
    improve_tuple_objects_with_name,
    replace_false_values,
    json_invalid_response,
    apply_compute_field_filters
)

from .decorators import (
    validate_token,
    validate_model_allowed,
    validate_record_id
)

from .variables import MODEL_ROUTE, RECORD_ROUTE, ATTACHMENT_ROUTE
_logger = logging.getLogger(__name__)


class APIController(http.Controller):

    def __init__(self):
        self._model = "ir.model"

    @validate_token
    @validate_model_allowed
    @http.route([MODEL_ROUTE, RECORD_ROUTE],
                type="http", auth="none", methods=["GET", "OPTIONS"], csrf=False)
    def get(self, model=None, record_id=None, **kwargs):
        model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        company = request.env['res.company'].sudo().browse(request.session['company'])
        domain, compute_domain, fields, field_filter, offset, limit, order = extract_arguments(kwargs, model=model)

        if not field_filter:
            fields = (model.api_fields and [f.name for f in model.api_fields]) or fields

        if record_id:
            records = request.env[model.model].sudo().browse(int(record_id))
        else:
            records = request.env[model.model].sudo().search(domain)

        if records:
            # If there are some computed fields need to be included, include now
            include_computed_fields(model=model, fields=fields)
            _logger.debug(records)

            read_data = request.env[model.model].with_company(company).sudo().search_read(
                domain=[('id', 'in', records.ids[:(limit or 20)])],
                fields=fields,
                offset=offset,
                limit=limit,
                order=order
            )
            logging.info("API search: data fetched successfully")

            # Cannot search by computed fields, so verify computed fields searched for via separate operation
            read_data = apply_compute_field_filters(data=read_data, compute_domain=compute_domain)

            # Replace field names if mapping alternative is provided in the settings
            replace_field_names(request=request, data=read_data, model=model.model)

            # Replace all False values the response with blank values
            if company.replace_false:
                replace_false_values(data=read_data)

            # Include fixed fields
            if not field_filter:
                include_fixed_fields(company=company, data=read_data, model=model.model)

            # Read lines and other related objects only when it's GET 1 object by ID
            # When no record_id specific, it's a search and we don't need to be too specific
            # Unless it's explicitly asked for the detailed response via the params
            if record_id or kwargs.get('detailed'):
                read_related_objects(data=read_data, model=model)
                improve_tuple_objects(data=read_data)

            elif kwargs.get('name_only'):
                read_related_objects(data=read_data, model=model)
                improve_tuple_objects_with_name(data=read_data)

            # Prepare datetime objects for returning (replace dt objects with local datetime strings)
            format_datetime(company=company, data=read_data, local_tz_name=request.session.get('tz'))

            return valid_response(read_data)

        return valid_response([])

    @validate_token
    @validate_model_allowed
    @http.route([MODEL_ROUTE], type="json", auth="none", methods=["POST", "OPTIONS"], csrf=False)
    def post(self, model=None, **kwargs):
        """Create a new record.

        Basic usage:
        import requests

        headers = {
            'Content-Type': 'application/json',
            'Access-Token': 'access_token'
        }

        params = {
            'partner_id': 1,
            'company': 1

        }
        req = requests.post('%s/api/v1/model/sale.order/' % base_url, headers=headers, data=data)

        """
        resource = {}
        company_id = request.session['company']
        user_id = request.session['user']

        try:
            model_obj = request.env[self._model].sudo().search([("model", "=", model)], limit=1)

            # Do some preparation of the payload
            payload = prepare_payload(
                payload=json.loads(request.httprequest.data.decode('utf-8')),
                api_fields=model_obj.api_fields
            )

            # Cater for both [] and {} data structure
            created = []
            if isinstance(payload, list):
                for obj in payload:
                    resource = request.env[model].with_company(company_id).with_context(
                        mail_create_nosubscribe=True
                    ).with_user(user_id).create(obj)
                    created.append(resource)
            else:
                resource = request.env[model].with_company(company_id).with_context(
                    mail_create_nosubscribe=True
                ).with_user(user_id).create(payload)
                created.append(resource)

            if not created:
                return json_invalid_response(
                    error_type="data",
                    message="Duplicated SO have been POSTed, ignoring the data.")

        except Exception as e:
            _logger.error(e)
            return json_invalid_response(
                error_type="data",
                message="Cannot handle this request, most likely the data POSTed is invalid/incorrect/incomplete"
            )

        return json_valid_response(
            data=get_post_return_data(resource),
            status=201,
            count=False
        )

    @validate_token
    @validate_record_id
    @validate_model_allowed
    @http.route([ATTACHMENT_ROUTE], type="json", auth="none", methods=["POST", "OPTIONS"], csrf=False)
    def post_attachment(self, model, record_id, **kwargs):
        """
        Add base64 file to a record as an attachment
        Works on POST only

        Data to post:
        {"attachments": [{"data": "base64 data", "name": "file name"}]}
        """
        company_id = request.session['company']
        user_id = request.session['user']

        try:
            payload = json.loads(request.httprequest.data.decode('utf-8'))
            record = request.env[model].sudo().browse(int(record_id))

            if record and payload.get('attachments'):

                for attach in payload['attachments']:
                    data = attach.get('data', '')
                    name = attach.get('name', 'no name')

                    request.env['ir.attachment'].with_company(company_id).with_user(user_id).create({
                        'datas': data,  # supposed to be base64 string
                        'name': name,
                        'res_id': int(record_id),
                        'res_model': model
                    })

        except Exception:
            return json_invalid_response(
                error_type="data",
                message="Cannot handle this request, most likely the data POSTed is invalid/incorrect/incomplete"
            )

        logging.info("Created attachments for Record {} with ID {}".format(model, record_id))

        return valid_response(
            data={"id": record.id, "model": record._name},
            status=201,
        )

    @validate_token
    @validate_record_id
    @validate_model_allowed
    @http.route([RECORD_ROUTE], type="json", auth="none", methods=["PUT", "OPTIONS"], csrf=False)
    def put(self, model, record_id, **kwargs):
        """
        Similar to POST endpoint, just need to pass record ID in
        It does update the existing record (if found by record ID) with the payload
        """
        company_id = request.session['company']
        user_id = request.session['user']

        try:
            model_obj = request.env[self._model].sudo().search([("model", "=", model)], limit=1)

            # Do some preparation of the payload
            payload = prepare_payload(
                payload=json.loads(request.httprequest.data.decode('utf-8')),
                api_fields=model_obj.api_fields
            )

            request.env[model].sudo().browse(int(record_id)).with_company(company_id).with_user(user_id).write(payload)

        except Exception:
            return json_invalid_response(
                error_type="data",
                message="Cannot handle this request, most likely the data in PUT is invalid/incorrect"
            )

        message = "Updated {} record with ID {} successfully".format(model, record_id)
        logging.info(message)

        return valid_response(message)

    @validate_token
    @validate_record_id
    @validate_model_allowed
    @http.route([RECORD_ROUTE], type="http", auth="none", methods=["DELETE", "OPTIONS"], csrf=False)
    def delete(self, model=None, record_id=None, **payload):
        """
        Delete an existing record (if found)
        Must pass a record ID
        """
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        delete_domain = _model.delete_domain

        try:
            found_without_delete_domain = False
            record = request.env[model].sudo().browse(int(record_id))

            if record:
                found_without_delete_domain = True

            if delete_domain:
                domain = safe_eval(delete_domain)
                domain.append(("id", "=", int(record_id)))
                record = request.env[model].sudo().search(domain)

            if record:
                record.unlink()

            else:
                if found_without_delete_domain:
                    logging.warning(
                        "DELETE a record {} ID {} when state is not allowed".format(
                            model, record_id
                        )
                    )
                    return invalid_response(
                        "cannot_delete",
                        "Record object with id {} cannot be deleted in its state".format(record_id), 403
                    )

                else:
                    logging.warning(
                        "DELETE a record {} ID {} which cannot be found".format(
                            model, record_id
                        )
                    )
                    return invalid_response(
                        "missing_record",
                        "record object with id {} could not be found".format(record_id), 404
                    )

        except Exception as e:
            logging.error("DELETE {} ID {} -- exception happened - {}".format(model, record_id, e))
            return invalid_response("exception", e, 503)

        return valid_response(
            {"success": "Record {0} successfully deleted for model {1}".format(record.id, record._name)},
        )
