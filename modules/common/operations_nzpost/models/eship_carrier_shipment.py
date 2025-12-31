import json
import requests

from datetime import datetime
from jinja2 import Template

import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.operations_courier_integration.api.api_client import CourierApiMixin
from ..eship_api.api_models import CarrierShipment, CarrierShipmentOrder, Package, Item, ShippingOptions
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

ORDER_CONTEXT = "orders"
LABEL_CONTEXT = "orders/shipment"
TRACKING_CONTEXT = "track"
RATES_CONTEXT = "rates"

CONFIG_SECTION = "eship-integration"
NZ_POST_SECTION = "operations-nzpost"

NZ_POST_AUTH_ENDPOINT = config.get(NZ_POST_SECTION, 'nzpost_auth_endpoint')
NZ_POST_ENDPOINT = config.get(NZ_POST_SECTION, 'nzpost_endpoint')
NZ_POST_CLIENT_ID = config.get(NZ_POST_SECTION, 'nzpost_client_id')
NZ_POST_SECRET = config.get(NZ_POST_SECTION, 'nzpost_secret')


CONFIG = {
    'headers': {
        'StarShipIT-Api-Key': config.get(CONFIG_SECTION, 'eship_api_key') or 'NOT FOUND',
        'Ocp-Apim-Subscription-Key': config.get(CONFIG_SECTION, 'eship_subscription_key') or 'NOT FOUND'

    },
    'endpoint': config.get(CONFIG_SECTION, 'eship_endpoint') or 'NOT FOUND'
}

NO_TRACKING_NUMBER = "No Tracking Number"

EVENTS_TEMPLATE = """
<table style="border: 1px solid grey; width: 100%">
    <tr>
        <th style="border: 1px solid grey; padding: 5px;">Date</th>
        <th style="border: 1px solid grey; padding: 5px;">Status</th>
        <th style="border: 1px solid grey; padding: 5px;">Details</th>
    </tr>
    {% for event in events %}
    <tr>
        <td style="border: 1px solid grey; padding: 5px;">{{event.date}}</td>
        <td style="border: 1px solid grey; padding: 5px;">{{event.status}}</td>
        <td style="border: 1px solid grey; padding: 5px;">{{event.details}}</td>
    </tr>
    {% endfor %}
</table>
"""
# Cannot specify a carrier to use via API. carrier is selected through mapping rules on eShip (Admin settings). The
# code is used in the mapping table
# (Carrier, 'service name', 'service code')
CARRIER_SERVICES = [('Courierpost', 'Online Parcel', 'CPOLP'),
                    ('Courierpost', 'Online Economy', 'CPOLE'),
                    ('Courierpost', 'Online Trackpak A4', 'CPOLTPA4'),
                    ('Courierpost', 'Online Trackpak A5', 'CPOLTPA5'),
                    ('Courierpost', 'Online Trackpak XL', 'CPOLTPLF')]


class EshipCarrierShipment(models.Model, CourierApiMixin):
    """eShip Shipment"""

    _name = "eship.carrier.shipment"
    _inherit = ["mail.thread", "carrier.shipment.abstract"]
    _description = 'eShip'

    @api.depends('json_post')
    def _compute_all(self):
        for line in self:
            if not line.json_post:
                continue
            data = json.loads(line.json_post)
            order = data['order']
            packages = order.get('packages', [])
            base_url = ''
            for package in packages:
                base_url = package.get('tracking_url', '')
                break
            tracking_ref = line.picking_id.carrier_tracking_ref or ''
            vals = {
                'eship_order_id': order.get('order_id', 0),
                'eship_order_number': order.get('order_number'),
                'carrier': order.get('carrier_name', ""),
                'errors': "",
                'notifications': "",
                'tracking_url': base_url + tracking_ref.split(',')[0],
                'consignment_nr': ""
            }
            line.update(vals)

    @api.depends('json_get')
    def _compute_delivery_status(self):
        for line in self:
            if not line.json_get:
                line.update({
                    'delivery_status': 'Unknown',
                    'delivery_date': '',
                    'delivery_events': ''
                })
                continue
            data = json.loads(line.json_get)

            events = []
            delivery_date = False
            for event in data.get('tracking_events', []):
                event_date = datetime.strptime(event.get('event_datetime', ""), "%Y-%m-%dT%H:%M:%S")
                event_date = fields.Datetime.to_string(event_date)
                item = {
                    'date': event_date,
                    'status': event.get('status') or "",
                    'details': event.get('details') or ""
                }
                events.append(item)
                if item['status'] == 'Delivered':
                    delivery_date = event_date

            vals = {
                'delivery_status': data.get('order_status') or 'Unknown',
                'delivery_date': delivery_date,
                'delivery_events': '',
            }

            if events:
                template = Template(EVENTS_TEMPLATE)
                res = template.render({'events': events})
                vals['delivery_events'] = res

            line.update(vals)

    eship_order_id = fields.Integer('eShip Order ID', compute='_compute_all')
    eship_order_number = fields.Char('Order Number', compute='_compute_all')
    return_shipment = fields.Many2one(_name, "Return Shipment", readonly=True, ondelete='set null')
    is_return_for = fields.Many2one(comodel_name=_name)

    @staticmethod
    def _is_dev_mode():
        return config.get(CONFIG_SECTION, "dev_mode", False)

    @api.depends('order_number')
    def _compute_display_name(self):
        for record in self:
            record.display_name = "{}:{}".format(record.order_number, record.eship_order_id)

    def create_shipment(self, ship_wizard):

        picking = ship_wizard.picking_id
        sale_order = picking.sale_id
        carrier_service = ship_wizard.service_id

        ref = picking.name
        shipment_order = CarrierShipmentOrder()
        order = shipment_order.order
        order.order_number = "*TEST({})".format(ref) if self._is_dev_mode() else ref
        order.reference = sale_order.name or ""
        order.shipping_method = carrier_service.delivery_type
        order.signature_required = ship_wizard.is_signature_required
        order.dangerous_goods = ship_wizard.is_dangerous_goods

        partner = picking.partner_id
        dest = order.destination
        dest.delivery_instructions = ship_wizard.delivery_instructions or ""
        dest.building = ship_wizard.building or ""

        if sale_order.alternate_shipping_address:
            pseudo_partner = ship_wizard.make_alternate_address_pseudo_partner()
            self._build_delivery_address(pseudo_partner, dest)
            dest.name = sale_order.alt_contact or partner.parent_id.name or partner.name
            dest.phone = sale_order.alt_phone or ""
        else:
            pseudo_partner = ship_wizard.make_address_pseudo_partner()
            self._build_delivery_address(pseudo_partner, dest)
            dest.name = partner.parent_id.name or partner.name
            dest.phone = partner.phone or ""

        if self._is_dev_mode():
            dest.name = "*TEST({})".format(dest.name)

        total_packages = 0
        total_weight = 0
        for p in ship_wizard.detail_ids:
            total_packages += p.qty
            for _ in range(p.qty):
                package = Package()
                package.weight = p.weight
                package.length = p.box_id.length / 100.0
                package.width = p.box_id.width / 100.0
                package.height = p.box_id.height / 100.0
                order.packages.append(package)
                total_weight += p.weight

        for move in picking.move_ids.filtered(lambda r: r.state == 'done'):
            item = Item()
            item.description = move.name.strip()
            item.sku = move.product_id.default_code or ""
            item.quantity = move.product_uom_qty
            item.weight = move.weight
            item.value = move.price_unit
            order.items.append(item)

        response = self.request_post(CONFIG, ORDER_CONTEXT, shipment_order.to_json())
        if not response:
            return self

        CarrierShipment.validate_shipment_post_response(response)
        shipment = self.create({'picking_id': picking.id,
                                'json_post': json.dumps(response),
                                'shipping_cost': carrier_service.cost})

        tracking_nrs = []
        for label in shipment.get_print_label_documents(tracking_nrs):
            name, label_data = label
            self.env['ir.attachment'].sudo().create({
                'datas': label_data,
                'store_fname': name + '.pdf',
                'name': name,
                'res_id': shipment.id,
                'res_model': shipment._name
            })

        picking_values = {
            'weight': total_weight,
            'shipping_weight': total_weight,
            'number_of_packages': total_packages
        }

        shipment._update_picking_fields(tracking_nrs=tracking_nrs, picking_values=picking_values)

        return shipment

    @api.model
    def _build_delivery_address(self, partner, address):

        address.street = partner.street or ""
        address.suburb = partner.street2 or ""
        address.city = partner.city or ""
        address.state = partner.state_id.name or ""
        address.post_code = partner.zip or ""
        address.country = partner.country_id.name or ""

    def get_print_label_documents(self, extracted_tracking_nrs):
        self.ensure_one()

        res = []

        label_request = {"order_id": self.eship_order_id}
        response = self.request_post(CONFIG, LABEL_CONTEXT, json.dumps(label_request))
        if not response:
            return res

        doc_data = []
        for tracking_nr in response.get("tracking_numbers", []):
            extracted_tracking_nrs.append(tracking_nr)

        for label_data in response.get("labels", []):
            doc_data.append(label_data)

        for pdf in doc_data:
            res.append(('print_label', pdf,))

        return res

    @api.model
    def _get_nz_post_access_token(self):
        url = '{endpoint}?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials'.format(
            endpoint=NZ_POST_AUTH_ENDPOINT,
            client_id=NZ_POST_CLIENT_ID,
            client_secret=NZ_POST_SECRET,
        )

        try:
            auth_response = requests.post(url)
            _logger.debug("url={}, response={}".format(url, auth_response.text))

            # Extract access token
            access_token = auth_response.json().get('access_token')

            if auth_response.status_code not in [200, 201, 202]:
                self._log_and_raise("invalid response, code={}".format(auth_response.status_code))
                return None

            return access_token

        except Exception as e:
            msg = "failure on endpoint={}, exception={}".format(url, e)
            _logger.error(msg)
            raise UserError(msg)

    def _get_nz_post_rates(self, ship_wizard, rates, access_token):
        url = ('{endpoint}?'
               'delivery_city={delivery_city}&'
               'delivery_postcode={delivery_postcode}&'
               'pickup_postcode={pickup_postcode}&'
               'pickup_suburb={pickup_suburb}&'
               'weight={weight}&'
               'length={length}&'
               'width={width}&'
               'height={height}'.format(
                    endpoint=NZ_POST_ENDPOINT,
                    delivery_city=rates.delivery_city,
                    delivery_postcode=rates.delivery_postcode,
                    pickup_postcode=ship_wizard.picking_id.picking_type_id.warehouse_id.partner_id.zip,
                    pickup_suburb=ship_wizard.picking_id.picking_type_id.warehouse_id.partner_id.street2,
                    weight=rates.weight,
                    length=int(rates.length) if (rates.length - int(rates.length) == 0) else int(rates.length),
                    width=int(rates.width) if (rates.width - int(rates.width) == 0) else int(rates.width),
                    height=int(rates.height) if (rates.height - int(rates.height) == 0) else int(rates.height),
               ))

        try:
            response = requests.get(url, headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token,
                'client_id': NZ_POST_CLIENT_ID
            })
            _logger.debug("url={}, response={}".format(url, response.text))

            if response.status_code not in [200, 201, 202]:
                self._log_and_raise("invalid response, code={}".format(response.status_code))
                return None

            return response.json()

        except Exception as e:
            msg = "failure on endpoint={}, exception={}".format(url, e)
            _logger.error(msg)
            raise UserError(msg)

    @api.model
    def get_available_services(self, ship_wizard):

        ship_model = self.env['eship.carrier.shipment']
        partner = ship_model._get_addr(ship_wizard.picking_id.partner_id, 'delivery')
        rates = ShippingOptions()

        if ship_wizard.alternate_address:
            so = ship_wizard.picking_id.sale_id
            rates.delivery_city = so.alt_city or ""
            rates.delivery_postcode = so.alt_zip or ""
        else:
            rates.delivery_city = partner.city or ""
            rates.delivery_postcode = partner.zip or ""

        rate_values = {}

        for p in ship_wizard.detail_ids:
            rates.weight = p.qty * p.weight
            rates.width = p.box_id.width
            rates.height = p.box_id.height
            rates.length = p.box_id.length

            access_token = self._get_nz_post_access_token()
            response = self._get_nz_post_rates(ship_wizard=ship_wizard, rates=rates, access_token=access_token)

            if not response:
                raise UserError("No or invalid response from eShip")

            ShippingOptions.validate_rates_get_response(response)
            rate_values[p] = self._get_services_from_response(response, ship_wizard)

        options_count = 0
        rate_options = {}

        for box, box_rates in rate_values.items():
            for rate in box_rates:
                if not options_count:
                    rate_options[rate['delivery_type']] = [rate]
                else:
                    if rate['delivery_type'] not in rate_options:
                        continue  # The same box must be as an option for all 3 boxes so we can add this all up together
                    rate_options[rate['delivery_type']].append(rate)
            options_count += 1

        if rate_options:
            services = self.env['delivery.carrier.service'].browse()

            for option_code, option_data in rate_options.items():
                option_dict = option_data[0]
                option_dict['cost'] = round(sum(op['cost'] for op in option_data), 2)
                services += services.create(option_dict)

            return services

    @api.model
    def _get_services_from_response(self, response, ship_wizard):
        available = response.get('services')
        values_list = []

        def _sanitize(text: str):
            return text.strip('\r\n ')

        if not available:
            return self.browse()  # Empty record set

        for service in available:
            if service.get('carrier') == 'Pace':  # Ignore Page couriers
                continue

            cost = service.get('price_excluding_gst', 0)

            # Include extra cost for Saturday delivery and signature required
            for addon in service.get('addons'):
                if addon.get('mandatory'):
                    cost += addon.get('price_excluding_gst', 0)

                if addon.get('addon_code') == 'CPSR' and ship_wizard.is_signature_required:
                    cost += addon.get('price_excluding_gst', 0)

                if addon.get('addon_code') == 'CPOLSAT' and ship_wizard.is_saturday_delivery:
                    cost += addon.get('price_excluding_gst', 0)

                if addon.get('addon_code') == 'CPOLDG' and ship_wizard.is_dangerous_goods:
                    cost += addon.get('price_excluding_gst', 0)

            values_list.append({
                'ship_wizard': ship_wizard.id,
                'services_request_iteration': ship_wizard.services_request_iteration,
                'quote_id': '',
                'carrier_name': 'Courier Post',
                'carrier_service': _sanitize(service.get('description', '')),
                'delivery_type': _sanitize(service.get('service_code', '')),
                'cost': round(cost, 2)
            })

        return values_list

    @api.model
    def create_return_shipment(self, outbound_shipment, ship_wizard):
        raise UserError("Return shipment functionality not supported by eShip")

    def update_shipment(self):
        self.ensure_one()

        if not self.eship_order_number:
            raise UserError("Shipment has no eShip Order Number")

        response = self.request_get(CONFIG, TRACKING_CONTEXT, {'order_number': self.eship_order_number})

        CarrierShipment.validate_shipment_get_response(response)

        result = response.get("results")
        if not result:
            return False

        self.json_get = json.dumps(result)
        self.last_updated = fields.Datetime.now()

        return True
