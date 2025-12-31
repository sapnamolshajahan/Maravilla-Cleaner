# -*- coding: utf-8 -*-

import json
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PDF_OUTPUT_TYPE = "LABEL_PDF_100X175"
PNG_OUTPUT_TYPE = "LABEL_PNG_100X175"


def _log_and_raise(msg):
    _logger.error(msg)
    raise UserError(msg)


class AutoJson(object):

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class CarrierShipment(AutoJson):

    def __init__(self):
        self.QuoteId = ""
        self.Carrier = ""
        self.Service = ""
        self.Origin = ""
        self.Destination = Destination()
        self.Packages = []
        self.IsSaturdayDelivery = False
        self.IsSignatureRequired = False
        self.DutiesAndTaxesByReceiver = False
        self.RuralOverride = True  # Ignore all rural delivery validation and surcharges
        self.DeliveryReference = ""
        self.Commodities = []
        self.PrintToPrinter = "false"
        self.Outputs = [PDF_OUTPUT_TYPE, PNG_OUTPUT_TYPE]
        self.HasDG = False
        self.DangerousGoods = None

    @staticmethod
    def _format_errors(errors):
        if not errors:
            return ""

        err_list = []
        for e in errors:
            err_list.append("{} - {}".format(e.get('Property', "Error"), e.get('Message', '')))
        details = "\n".join(err_list)

        return details

    @staticmethod
    def validate_shipment_post_response(response):
        if "Errors" not in response:
            _logger.error('Unexpected response from server:\n' + str(response))
            raise UserError('Unexpected response from server')
        if response.get('Errors', []):
            msg = 'The following error occurred when creating the shipment:\n'
            details = CarrierShipment._format_errors(response['Errors'])
            _log_and_raise(msg + details)

        return True

    @staticmethod
    def validate_shipment_get_response(response):
        # TODO: add validation as needed
        return True


class InboundCarrierShipment(AutoJson):

    def __init__(self):
        self.Carrier = ""
        self.Service = ""
        self.Origin = InboundOrigin()
        self.Destination = InboundDestination()
        self.Packages = []
        self.IsSaturdayDelivery = False
        self.IsSignatureRequired = False
        self.IsUrgentCouriers = False
        self.DutiesAndTaxesByReceiver = False
        self.DeliveryReference = ""
        self.Commodities = []
        self.PrintToPrinter = "false"
        self.Outputs = [PDF_OUTPUT_TYPE]
        self.CarrierId = 0
        self.IncludeLineDetails = False
        self.ShipType = 1
        self.HasDG = False
        self.DangerousGoods = None
        self.DisableFreightForwardEmails = True
        self.IncludeInsurance = False

    @staticmethod
    def _format_errors(errors):
        if not errors:
            return ""

        err_list = []
        for e in errors:
            err_list.append("{} - {}".format(e.get('Property', "Error"), e.get('Message', '')))
        details = "\n".join(err_list)

        return details

    @staticmethod
    def validate_shipment_post_response(response):
        if "Errors" not in response:
            _logger.error('Unexpected response from server:\n' + str(response))
            raise UserError('Unexpected response from server')
        if response.get('Errors', []):
            msg = 'The following error occurred when creating the return shipment:\n'
            details = CarrierShipment._format_errors(response['Errors'])
            _log_and_raise(msg + details)

        return True


class ServiceRates(AutoJson):
    def __init__(self):
        self.DeliveryReference = ""
        self.Destination = RatesDestination()
        self.IsSaturdayDelivery = False
        self.IsSignatureRequired = False
        self.Packages = []

    @staticmethod
    def validate_rates_post_response(response):
        if response.get('ValidationErrors', {}):
            msg = 'The following error occurred while requesting available services:\n'
            details = response.get('ValidationErrors', {})
            text = ""
            for k, v in details.items():
                text += "{}:{}\n".format(k, v)
            _log_and_raise(msg + text)

        return True


class RatesDestination(AutoJson):
    def __init__(self):
        self.Name = ""
        self.Id = 0
        self.ContactPerson = ""
        self.PhoneNumber = ""
        self.DeliveryInstructions = ""
        self.Email = ""
        self.Address = Address()


class Destination(AutoJson):
    def __init__(self):
        self.Name = ""
        self.ContactPerson = ""
        self.PhoneNumber = ""
        self.IsRural = False
        self.DeliveryInstructions = ""
        self.SendTrackingEmail = False
        self.CostcentreId = None
        self.ExplicitNotRural = False
        self.Address = Address()
        self.Email = ""


class InboundOrigin(AutoJson):
    def __init__(self):
        self.Name = ""
        self.ContactPerson = ""
        self.PhoneNumber = ""
        self.IsRural = False
        self.DeliveryInstructions = ""
        self.SendTrackingEmail = False
        self.Address = Address()
        self.Email = ""


class InboundDestination(InboundOrigin):
    def __init__(self):
        super(InboundDestination, self).__init__()
        self.SendTrackingEmail = False


class Address(AutoJson):

    def __init__(self):
        self.BuildingName = ""
        self.StreetAddress = ""
        self.Suburb = ""
        self.City = ""
        self.Postcode = ""
        self.CountryCode = "NZ"


class Package(AutoJson):

    def __init__(self):
        self.Name = "custom"
        self.Kg = 1
        self.Height = 0
        self.Width = 0
        self.Length = 0
        self.Type = ""
