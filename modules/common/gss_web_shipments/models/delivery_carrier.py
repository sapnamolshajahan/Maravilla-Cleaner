# -*- coding: utf-8 -*-
import logging
import json
from odoo import models
from odoo.tools.config import config
from odoo.exceptions import UserError
from odoo.addons.operations_gss_integration.gss_api.api_models import ServiceRates, Package

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"


    def get_gss_shipping_rate(self, order):

        if not order.partner_shipping_id:
            raise UserError("Shipping address is missing in the order.")

        partner = order.partner_shipping_id
        gss_model = self.env['gss.carrier.shipment'].sudo()

        rates = ServiceRates()
        rates.DeliveryReference = order.name or "WEB"
        rates.IsSaturdayDelivery = False
        rates.IsSignatureRequired = False

        dest = rates.Destination
        dest.Name = partner.parent_id.name or partner.name
        dest.ContactPerson = partner.name or ""
        dest.PhoneNumber = partner.phone or ""
        dest.Email = partner.email or ""

        addr = dest.Address
        addr.StreetAddress = partner.street or ""
        addr.Suburb = partner.street2 or ""
        addr.City = partner.city or ""
        addr.Postcode = partner.zip or ""
        addr.CountryCode = partner.country_id.code or "NZ"

        total_weight = sum([
            line.product_id.weight * line.product_uom_qty
            for line in order.order_line if line.product_id.type == 'product'
        ])
        if not total_weight:
            total_weight = 1.0

        # TO DO: Have this calculate dimensions from products/delivery packages
        pkg = Package()
        pkg.Kg = total_weight
        pkg.Length = 10
        pkg.Width = 10
        pkg.Height = 10
        pkg.Name = "AutoPackage"
        rates.Packages.append(pkg)

        config = gss_model._get_api_config(None)
        response = gss_model.request_post(config, 'rates', rates.to_json())

        _logger.info("GSS API Response:", json.dumps(response, indent=4))

        if not response or 'Available' not in response:
            return False

        available = response['Available']
        if not available:
            return False

        best_service = min(available, key=lambda r: r.get('Cost', float('inf')))
        return best_service.get('Cost', 0.0)


    def gss_rate_shipment(self, order):
        res = self.get_gss_shipping_rate(order)
        if res or res == 0:
            return {'success': True,
                    'price': res,
                    'error_message': False,
                    'warning_message': False}
        else:
            return {'success': False,
                    'price': 0,
                    'error_message': 'Something Went Wrong!',
                    'warning_message': 'Something Went Wrong!'}
