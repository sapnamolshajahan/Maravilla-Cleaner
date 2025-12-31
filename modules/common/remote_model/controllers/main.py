# -*- coding: utf-8 -*-
import base64
import logging

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from odoo import http, SUPERUSER_ID
from odoo.api import Environment
from odoo.http import request
from odoo.modules.registry import Registry
from ..config import PRIVATE_KEY, PUBLIC_KEYS
from ..exceptions import InvalidConfiguration

API_VERSION = 16  # should match Odoo version
REMOTE_PROXY_HEADER_SIG = "OptimySME-remote-model-signature"

_logger = logging.getLogger(__name__)


class RemoteModelController(http.Controller):
    """
    Services for remote_model
    """

    @http.route(f"/remote_model/{API_VERSION}/search/<dbname>", type="json", auth="none")
    def incoming_search(self, dbname, model, domain, offset, order, limit):
        """
        The arguments after 'dbname' are unpacked from the POST against the URL.

        :rtype: list of ids
        """
        validate_signature(request.httprequest.data, request.httprequest.headers.get(REMOTE_PROXY_HEADER_SIG))

        with Registry(dbname).cursor() as cr:
            q_env = self._query_env(cr)

            records = q_env[model].search(domain, offset, limit, order)
            result = [r.id for r in records]
        return result

    @http.route(f"/remote_model/{API_VERSION}/read/<dbname>", type="json", auth="none")
    def incoming_read(self, dbname, model, ids, fields):
        """
        The arguments after 'dbname' are unpacked from the POST against the URL.
        """
        validate_signature(request.httprequest.data, request.httprequest.headers.get(REMOTE_PROXY_HEADER_SIG))

        with Registry(dbname).cursor() as cr:
            q_env = self._query_env(cr)

            result = {}
            for rec in q_env[model].browse(ids).read(fields):
                values = {}
                for name in fields:
                    field = q_env[model]._fields[name]
                    if field.type == "many2one":
                        values[name] = rec[name][0] if rec[name] else False
                    else:
                        values[name] = rec[name]
                result[rec["id"]] = values

        return result

    def _query_env(self, cr):
        return Environment(cr, SUPERUSER_ID, {})


def validate_signature(data, b64_signature):
    """
    Validate signature
    :param data: byte[]
    :return: path of validating key
    """
    signature = base64.b64decode(b64_signature)

    for pk in PUBLIC_KEYS:
        path = pk["path"]
        key = pk["key"]
        try:
            key.verify(
                signature, data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())
            _logger.debug(f"accept key={path}")
            return path

        except InvalidSignature:
            _logger.debug(f"nope, it's not key={path}")

    raise InvalidConfiguration("remote_model signature is invalid")


def b64_signature(data):
    """
    Sign data with private key.

    :param data: byte[]
    :return: b64 encoded signature
    """
    signature = PRIVATE_KEY.sign(data,
                                 padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                                 hashes.SHA256())
    return base64.b64encode(signature).decode("utf-8")
