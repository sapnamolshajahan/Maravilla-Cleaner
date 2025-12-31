# -*- coding: utf-8 -*-

import json
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


def _log_and_raise(msg):
    _logger.error(msg)
    raise UserError(msg)


class AutoJson(object):

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class CarrierShipmentOrder(AutoJson):
    def __init__(self):
        self.order = CarrierShipment()


class CarrierShipment(AutoJson):

    def __init__(self):
        self.order_number = ""
        self.order_date = ""
        self.reference = ""
        self.signature_required = False
        self.shipping_method = "Standard"
        self.destination = Destination()
        self.items = []
        self.packages = []

    #TODO: All validation to be tested
    @staticmethod
    def _format_errors(errors):
        if not errors:
            return ""

        err_list = []
        for e in errors:
            err_list.append("{} - {}".format(e.get('Property', 'Error'), e.get('details', '')))
        details = "\n".join(err_list)

        return details

    @staticmethod
    def validate_shipment_post_response(response):
        if not response.get('success'):
            if response.get('errors', []):
                msg = 'The following error occurred when creating the shipment:\n'
                details = CarrierShipment._format_errors(response['errors'])
                _log_and_raise(msg + details)
            else:
                _logger.error('Unexpected response from server:\n' + str(response))
                raise UserError('Unexpected response from server')

        return True

    @staticmethod
    def validate_shipment_get_response(response):
        # TODO: add validation as needed
        return True


class Destination(AutoJson):

    def __init__(self):
        self.name = ""
        self.phone = ""
        self.street = ""
        self.suburb = ""
        self.city = ""
        self.state = ""
        self.post_code = ""
        self.country = "New Zealand"
        self.delivery_instructions = ""
        self.building = ""


class Item (AutoJson):

    def __init__(self):
        self.description = ""
        self.sku = ""
        self.quantity = 1
        self.weight = 1
        self.value = 0


class Package (AutoJson):

    def __init__(self):
        self.package_id = 0
        self.weight = 1
        self.height = 0
        self.width = 0
        self.length = 0


class Rates(AutoJson):

    def __init__(self):
        self.street = ""
        self.post_code = ""
        self.country_code = "NZ"
        self.suburb = ""
        self.city = ""
        self.weight = 0

    @staticmethod
    def validate_rates_get_response(response):
        success = response.get('success')
        if not success:
            _log_and_raise("eShip rates request failed")
        return True


class ShippingOptions(AutoJson):

    def __init__(self):
        self.weight = 0
        self.length = 0
        self.width = 0
        self.height = 0
        self.delivery_city = ""
        self.delivery_postcode = ""
        self.pickup_postcode = ""
        self.pickup_suburb = ""

    @staticmethod
    def validate_rates_get_response(response):
        success = response.get('success')

        if not success:
            _log_and_raise("eShip rates request failed")

        return True
