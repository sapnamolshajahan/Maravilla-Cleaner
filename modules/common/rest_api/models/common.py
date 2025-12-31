import json
import pytz
import logging

from datetime import date, datetime

import werkzeug.wrappers

from odoo.http import Response, request, HttpDispatcher
from odoo.exceptions import  MissingError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from ..controllers.variables import ALLOWED_HEADERS, ALLOWED_AUTH_HEADERS, ORIGIN
from ..controllers.variables import RECORD_ROUTE, MODEL_ROUTE, ATTACHMENT_ROUTE, LOGIN_ROUTE


_logger = logging.getLogger(__name__)


# Some tech fields not for return to the user
EXCLUDE_FIELDS = [
    '__last_update',
    'write_date',
    'create_date',
    'date',
    'tz',
    'reply_to',
    'message_ids',
    'message_follower_ids',
    'message_main_attachment_id',
    'message_needaction_counter',
    'message_needaction',
    'message_unread_counter',
    'message_has_error_counter',
    'message_is_follower',
    'message_has_error',
    'message_attachment_count',
    'message_unread',
]


def get_cors_headers():
    """FInd out what headers to pass on depending on route"""
    headers = {
        "Access-Control-Allow-Origin":  ORIGIN,
        "Access-Control-Allow-Headers": ALLOWED_HEADERS,
    }

    # Tune headers based on routes
    routes = request.endpoint.routing.get('routes')

    if routes == [LOGIN_ROUTE]:
        headers['Access-Control-Allow-Headers'] = ALLOWED_AUTH_HEADERS

    if routes == [MODEL_ROUTE]:
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    elif routes == [ATTACHMENT_ROUTE]:
        headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"

    elif routes == [RECORD_ROUTE]:
        headers["Access-Control-Allow-Methods"] = "GET, PUT, DELETE, OPTIONS"

    elif routes == [MODEL_ROUTE, RECORD_ROUTE]:
        headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"

    return headers


def options_response():
    """Valid Response for OPTIONS request"""

    return werkzeug.wrappers.Response(
        status=200,
        content_type="application/json; charset=utf-8"
    )


def valid_response(data, status=200):
    """Valid Response
    This will be return when the http request was successfully processed."""
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(data),
    )


def json_valid_response(data, status=200, count=True):
    """
    Valid Response
    This will be return when the request was successfully processed.
    """
    # Make sure response has the correct status
    Response._status_code = str(status)

    if count:
        data['count'] = len(data)

    return data


def invalid_response(error_type, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""

    # Format Odoo error message into the API suitable format
    error_type, message = parse_odoo_exception(message, error_type)

    headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}

    res = werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        headers=headers,
        response=json.dumps({
            "type": error_type,
            "message": (message and str(message)) or "Wrong arguments (missing validation)"
        })
    )

    return res


def json_invalid_response(error_type, message=None):
    """
    Invalid Response
    This will be the return value whenever the server runs into an error either from the client or the server.
    """
    # Format Odoo error message into the API suitable format
    error_type, message = parse_odoo_exception(message, error_type)

    return {
        "error": True,
        "error_type": error_type,
        "message": (message and str(message)) or "Wrong arguments (missing validation)",
    }


def extract_arguments(payloads, offset=0, limit=0, order=None, model=None):
    domain, compute_domain, payload = [], [], (payloads or {})

    try:
        payload = json.loads(str(payload))
    except Exception as e:
        _logger.error(e)

    payload_domain = payload.get("domain")

    if payload_domain:

        if ';' in payload_domain:
            domains = payload_domain.split(';')
        else:
            domains = [payload_domain]

        for each_domain in domains:
            what, operator, value = each_domain.split(',')

            if "|" in value:
                value = value.split("|")

            if model:
                field_object = request.env['ir.model.fields'].sudo().search([
                    ('model', '=', model.model),
                    ('name', '=', what)
                ])

                if hasattr(value, "isdigit") and value.isdigit() and (field_object.relation or field_object.ttype in ('float', 'integer')):
                    value = int(value)
                elif isinstance(value, list):
                    value = [int(value) for v in value]
                elif value == "False":
                    value = bool(value)

                # Separate stored fields searched in a separate domain to be applied separately
                # As normal odoo search cannot be used with computed non-stored fields
                if not field_object.store:  # i.e. it's a computed field
                    compute_domain.append(tuple([what, operator, value]))
                else:
                    domain.append(tuple([what, operator, value]))

    if payload.get("fields"):
        fields = payload.get('fields').replace(' ', '').split(',')
        field_filter = True
    else:
        fields = get_all_fields_without_excluded(model)
        field_filter = False

    if payload.get("offset"):
        offset = int(payload["offset"])

    if payload.get("limit"):
        limit = int(payload.get("limit"))

    if payload.get("order"):
        order = payload.get("order")

    return [domain, compute_domain, fields, field_filter, offset, limit, order]


def apply_compute_field_filters(data, compute_domain):
    if not compute_domain:
        return data

    cleaned_data = []

    for each_domain in compute_domain:
        what, operator, value = each_domain[0], each_domain[1], each_domain[2]

        # i.e. we support only = and != operations, skip anything we're not familiar with
        if operator == '=':
            equals = True

        elif operator == '!=':
            equals = False

        else:
            continue

        for data_obj in data:
            if equals:
                if data_obj.get(what) == value:
                    cleaned_data.append(data_obj)
            else:
                if data_obj.get(what) != value:
                    cleaned_data.append(data_obj)

    return cleaned_data


def handle_each_obj(payload_data, model_fields):
    for key, value in payload_data.items():

        if model_fields:
            this_field = model_fields.filtered(lambda f: f.name == key)

            # Replace obj ref if this is said to do so in the config
            if this_field and this_field.post_ref != 'id':
                actual_obj = request.env[this_field.relation].sudo().search([(this_field.post_ref, '=', value)])
                # Exact match for cases like product codes etc.
                actual_obj = actual_obj.filtered(lambda f: getattr(f, this_field.post_ref) == value)

                if len(actual_obj) > 1:
                    raise Exception(
                        'You are trying to link the object using a non-unique field, it will not work.\n'
                        'Field: value is {}:{}'.format(key, value))

                if actual_obj:
                    payload_data[key] = actual_obj.id

        if not value:
            continue

        if isinstance(value, list) and isinstance(value[0], dict):
            payload_data[key] = [(0, 0, each) for each in value]


def handle_one2many_data(payload, api_fields):
    """Pre-process one2many data and replace POST/PUT references if required"""
    for key, value in payload.items():
        if isinstance(value, list):
            object_list = []
            field_definition = api_fields.filtered(lambda x: x.name == key)

            if not field_definition or not field_definition.relation:
                continue

            related_model = request.env['ir.model'].sudo().search([('model', '=', field_definition.relation)])

            for obj in value:
                if isinstance(obj, tuple) and len(obj) == 3:
                    obj = obj[2]

                handle_each_obj(payload_data=obj, model_fields=related_model.field_id)
                object_list.append((0, 0, obj))
            payload[key] = object_list

def prepare_payload(payload, api_fields=None):
    # To cater for multiple objects at once - supports both {} and {"post_data": [{}, ...]} structures for POST
    if payload.get('post_data') and isinstance(payload['post_data'], list):
        return_data = []

        for obj in payload['post_data']:
            handle_each_obj(payload_data=obj, model_fields=api_fields)
            return_data.append(obj)

        return return_data

    handle_each_obj(payload_data=payload, model_fields=api_fields)
    handle_one2many_data(payload=payload, api_fields=api_fields)

    return payload


def read_related_objects(data, model):
    """
    :param data: list of dicts() with data read for the return
    """
    for obj in data:
        for key, value in obj.items():

            if (not isinstance(value, list)) or (not all(isinstance(item, int) for item in value)):
                continue

            # Get related field object by the key
            field_object = request.env['ir.model.fields'].sudo().search([
                ('model', '=', model.model),
                ('name', '=', key)
            ])

            # Get the model of the field so we can check API fields
            field_model = request.env['ir.model'].sudo().search([('model', '=', field_object.relation)])

            # So in search_read we'll narrow down to fields if they specified
            # Otherwise -- read all , this is what fields=[] means
            if field_model.api_fields:
                fields = [f.name for f in field_model.api_fields]
            else:
                fields = get_all_fields_without_excluded(field_model)

            # If there are some computed fields need to be included, include now
            include_computed_fields(model=field_model, fields=fields)

            # Read the field object now and assign it to the key in the return dict
            fields = list(set(fields) - set(EXCLUDE_FIELDS))
            read_obj = request.env[field_object.relation].sudo().search_read([('id', 'in', value)], fields=fields)
            obj[key] = read_obj


def improve_tuple_objects(data):
    """
    When Odoo does read_data(), it returns Many2one objects as tuples like:
    (7177, u'Company Name') -- where 7177 is object ID

    For better usability of the API, convert it into dict like:
    {'id': 7177, 'name': 'Company Name'}
    """
    for data_set in data:
        for key, value in data_set.items():

            if isinstance(value, tuple):
                data_set[key] = {'id': value[0], 'name': value[1]}


def improve_tuple_objects_with_name(data):
    """
    When Odoo does read_data(), it returns Many2one objects as tuples like:
    (7177, u'Company Name') -- where 7177 is object ID

    For better usability of the API, extract the name and return like:
    key: value
    """
    for data_set in data:
        for key, value in data_set.items():

            if isinstance(value, tuple):
                data_set[key] = value[1]


def include_computed_fields(model, fields):
    """
    Computed and non-stored fields are not available for selection for the API in the model config
    There is a special field for that: include_computed_fields
    Fields specified in "include_computed_fields" need to be included in the response as well

    :param model: ir.model object
    :param model: fields: list of fields search will be performed for

    """
    if not model.include_computed_fields:
        return fields

    incl_fields = [f.strip() for f in model.include_computed_fields.split(',')]
    fields.extend(list(set(incl_fields)))


def get_all_fields_without_excluded(model):
    """
    For cases when no specific fields, and we include all fields in the response
    Still, some tech fields must be excluded
    So, prepare fields by excluding the ones we don't want to include
    """
    all_fields = [f.name for f in request.env['ir.model.fields'].sudo().search([('model', '=', model.model)])]
    return list(set(all_fields) - set(EXCLUDE_FIELDS))


def parse_odoo_exception(message, error_type):
    """
    Format Odoo error message into the API suitable format
    :param message: str() or None
    :param error_type: int() or None
    :return:  parsed error message (if needs to be parsed) or same message and error type
    """
    if message:
        if isinstance(message, (MissingError, ValidationError)):
            return message

        elif isinstance(message, Warning):
            raise Warning(message)


    return error_type, message


def get_post_return_data(resource):
    """
    Include IDs of extra fields specified for model settings
    :param resource: object to include fields for

    """
    # Default return data
    data = {
        "success": True,
        "id": hasattr(resource, 'id') and resource.id or None,
        "model": resource._name,
    }

    if hasattr(resource, 'name'):
        data['name'] = resource.name

    model = request.env['ir.model'].sudo().search([("model", "=", resource._name)], limit=1)

    if model.include_fields_in_post_response:
        incl_fields = [f.strip() for f in model.include_fields_in_post_response.split(',')]

        for field in incl_fields:

            # In case field name entered does not exist
            if not hasattr(resource, field):
                continue

            data[field] = getattr(resource, field).ids

    return data


def format_datetime(company, data, local_tz_name):
    """
    :param company: res.company object
    :param data: list of dict() where each dict() is a data row
    :param local_tz_name: standard name of TZ for dates conversion
    :return updated data with datetime objects replaced with strings
    """

    def convert_datetime(datetime_object):

        if isinstance(datetime_object, date):
            return datetime_object.strftime(DEFAULT_SERVER_DATE_FORMAT)

        local_tz = pytz.timezone(local_tz_name)
        local_time = datetime_object.astimezone(local_tz)

        # Use custom format, if specified in the company config; otherwise default to a system format
        date_format = company.date_format or DEFAULT_SERVER_DATETIME_FORMAT
        return local_time.strftime(date_format)

    for row in data:
        for key, value in row.items():

            if isinstance(value, (date, datetime)):
                row[key] = convert_datetime(value)

            elif isinstance(value, list):
                # this means we're dealing with line items
                # go line by line (each line = dictionary) and check all values
                # if any date time objects in line values -> convert to strings as well
                for line_item in value:
                    if isinstance(line_item, dict):
                        for line_item_key, line_item_value in line_item.items():
                            if isinstance(line_item_value, (date, datetime)):
                                line_item[line_item_key] = convert_datetime(line_item_value)


def replace_field_names(request, data, model):
    """
    Check if there is a custom API mapping field for fields returned
    Replace, if there is a mapping set for the field
    """

    for obj in data:

        fields = {
            name: request.env['ir.model.fields'].sudo().search([
                ('name', '=', name),
                ('model', '=', model),
            ]) for name in obj.keys()
        }

        for old_name, field in fields.items():
            if field.api_name:
                obj[field.api_name] = obj.pop(old_name)


def include_fixed_fields(company, data, model):
    """
    Check if there are fixed fields set for this model to be included in the API response
    """
    include_fields = company.api_fields.filtered(lambda f: f.model.model == model and f.is_active)

    for obj in data:
        for field in include_fields:
            obj[field.name] = field.value


def replace_false_values(data):
    for obj in data:
        for key, value in obj.items():
            if value is False:
                obj[key] = ''
