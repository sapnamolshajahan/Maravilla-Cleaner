# -*- coding: utf-8 -*-
import logging

import requests
from requests.exceptions import ConnectionError

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

GET_TIMEOUT_MAX = 180
POST_TIMEOUT_MAX = 180


class CourierApiMixin(models.AbstractModel):
    """
    Mixin for courier implementations
    """
    _name = "courier.integration.api"
    _description = __doc__

    @staticmethod
    def _log_and_raise(msg):
        _logger.error(msg)
        raise UserError(msg)

    def request_get(self, conf, context, data):
        """
        Does a GET request
        Args:
            conf: MUST be a dictionary containing the following:
            {headers: {key:val,key:val}
             endpoint: 'base endpoint'
             }
            context: the resource that will be appended to endpoint url
            data: Dictionary for keyword args sent with the GET request

        Returns: JSON response as python dict

        """
        url = "{}/{}".format(conf.get('endpoint'), context)
        try:
            headers = conf.get('headers')
            response = requests.get(url, params=data,
                                    headers=headers,
                                    timeout=GET_TIMEOUT_MAX)
            _logger.debug("url={}, response={}".format(response.url, response.text))
            if response.status_code != 200:
                msg = "No information"
                if hasattr(response, 'message'):
                    msg = response.message
                self._log_and_raise("invalid response, code={}, Reason={}".format(response.status_code, msg))
                return None

            json_response = response.json()
            return json_response

        except ConnectionError as e:
            self._log_and_raise("failure on endpoint={}, exception={}".format(url, e))
        return None

    def request_post(self, conf, context, data):
        """
        Does a POST request
        Args:
            conf: MUST be a dictionary containing the following:
            {headers: {key:val,key:val}
             endpoint: 'base endpoint'
             }
            context: the resource that will be appended to endpoint url
            data: JSON data to be sent with the POST request

        Returns: JSON response as python dict

        """
        url = "{}/{}".format(conf.get('endpoint'), context)
        try:
            headers = {"Content-Type": "application/json"}
            headers.update(conf.get('headers'))
            response = requests.post(url, data=data,
                                     headers=headers,
                                     timeout=POST_TIMEOUT_MAX)
            _logger.debug("url={}, response={}".format(url, response.text))
            if response.status_code not in [200, 201, 202]:
                self._log_and_raise("invalid response, code={}".format(response.status_code))
                return None

            json_response = response.json()
            return json_response

        except ConnectionError as e:
            self._log_and_raise("failure on endpoint={}, exception={}".format(url, e))
        return None
