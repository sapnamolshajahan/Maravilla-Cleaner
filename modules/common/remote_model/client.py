# -*- coding: utf-8 -*-
import json
import logging

import requests

from odoo.addons.base_generic_changes.utils.config import configuration
from .config import SECTION_NAME, KEY_URL, KEY_DBNAME, PRIVATE_KEY
from .controllers.main import API_VERSION, REMOTE_PROXY_HEADER_SIG, b64_signature
from .exceptions import CodeFail, InvalidConfiguration, RemoteEndFailed, WhatTheHeck

POST_TIMEOUT_MAX = 180

_logger = logging.getLogger(__name__)


class RemoteProxyClient():
    """
    Talks to the other side
    """

    def __init__(self):
        self.url = None
        self.dbname = None
        self.remote_model = None

    def _validate_config(self, model):
        def config_lookup(prefix, name):
            key = prefix + name
            value = configuration.get(SECTION_NAME, key)
            if not value:
                raise InvalidConfiguration(f"Missing \"{key}\" in [{SECTION_NAME}]")
            return value

        if not model._remote_name:
            raise CodeFail(f"_remote_name not specified on model={model._name}")
        if not PRIVATE_KEY:
            raise InvalidConfiguration(f"Missing private_key in [{SECTION_NAME}]")

        sections = model._remote_name.split(":")
        sections_len = len(sections)
        if sections_len == 1:
            prefix = ""
            self.remote_model = sections[0]
        elif sections_len == 2:
            prefix = sections[0] + "_"
            self.remote_model = sections[1]
        else:
            raise CodeFail(f"Invalid _remote_name={model._remote_name} on model={model._name}")

        self.url = config_lookup(prefix, KEY_URL)
        self.dbname = config_lookup(prefix, KEY_DBNAME)

    def search(self, model, domain, offset, limit, order):
        """
        return list of ids
        """
        self._validate_config(model)
        return self._post("search",
                          {
                              "model": self.remote_model,
                              "domain": domain,
                              "offset": offset,
                              "limit": limit,
                              "order": order,
                          })

    def read(self, recordset, fields):
        """
        return list of dict-values
        """
        self._validate_config(recordset)
        return self._post("read",
                          {
                              "model": self.remote_model,
                              "ids": recordset.ids,
                              "fields": fields,
                          })

    def _post(self, entry, payload):
        """
        Manually build a JSON-RPC request and post it.
        """
        json_rpc = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "search",
            "params": payload,
        }
        endpoint = f"{self.url}/remote_model/{API_VERSION}/{entry}/{self.dbname}"
        data = json.dumps(json_rpc)
        signature = b64_signature(bytes(data, "utf-8"))
        try:
            headers = {
                "Content-Type": "application/json",
                REMOTE_PROXY_HEADER_SIG: signature,
            }
            # _logger.debug(f"post url={endpoint}, data={data}")
            response = requests.post(endpoint, data=data, headers=headers, timeout=POST_TIMEOUT_MAX)
            if response.status_code not in [200, 201, 202]:
                _logger.error(f"invalid response endpoint={endpoint}, code={response.status_code}")
                raise WhatTheHeck(f"endpoint={endpoint}, response={response.status_code}")

            json_response = response.json()

        except ConnectionError as e:
            _logger.error(f"failure on endpoint={endpoint}, exception={e}")
            raise e

        if "error" in json_response:
            error = json_response["error"]
            message = "?"
            if "data" in error and "message" in error["data"]:
                message = error["data"]["message"]
            raise RemoteEndFailed(message)

        return json_response["result"]
