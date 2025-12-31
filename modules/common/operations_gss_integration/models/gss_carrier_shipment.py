# -*- coding: utf-8 -*-
import base64
import io
import json
import logging
from datetime import datetime

from PIL import Image
from jinja2 import Template

from odoo import api, fields, models
from odoo.addons.operations_courier_integration.models.label_printer import MIMETYPE_BIN, MIMETYPE_PDF, MIMETYPE_PNG
from odoo.exceptions import UserError
from odoo.addons.base_generic_changes.utils.config import configuration
from ..gss_api.api_models import CarrierShipment, InboundCarrierShipment, Package, ServiceRates
from ..gss_api.api_models import PDF_OUTPUT_TYPE, PNG_OUTPUT_TYPE

_logger = logging.getLogger(__name__)

ORDER_CONTEXT = "shipments"
SERVICES_CONTEXT = "availableservices"
RATES_CONTEXT = "rates"

CONFIG_SECTION = "go-sweet-spot-integration"
CONFIG = {
    'headers': {
        'ACCESS_KEY': configuration.get(CONFIG_SECTION, 'api_key', fallback="0"),
        'SUPPORT_EMAIL': configuration.get(CONFIG_SECTION, 'email_id', fallback="0")
    },
    'endpoint': configuration.get(CONFIG_SECTION, 'api_endpoint', fallback="0")
}

NO_TRACKING_NUMBER = "No Tracking Number"

EVENTS_TEMPLATE = """
<table style="border: 1px solid grey; width: 100%">
    <tr>
        <th style="border: 1px solid grey; padding: 5px;">Date</th>
        <th style="border: 1px solid grey; padding: 5px;">Description</th>
        <th style="border: 1px solid grey; padding: 5px;">Location</th>
        <th style="border: 1px solid grey; padding: 5px;">Part</th>
    </tr>
    {% for event in events %}
    <tr>
        <td style="border: 1px solid grey; padding: 5px;">{{event.date}}</td>
        <td style="border: 1px solid grey; padding: 5px;">{{event.description}}</td>
        <td style="border: 1px solid grey; padding: 5px;">{{event.location}}</td>
        <td style="border: 1px solid grey; padding: 5px;">{{event.part}}</td>
    </tr>
    {% endfor %}
</table>
"""


class GssCarrierShipment(models.Model):
    """
    Go Sweet Spot Shipment
    """
    _name = "gss.carrier.shipment"
    _inherit = ["mail.thread", "carrier.shipment.abstract", "courier.integration.api"]
    _description = 'Carrier Shipment (GSS)'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    @api.depends('json_post')
    def _compute_all(self):
        for line in self:
            if not line.json_post:
                continue
            data = json.loads(line.json_post)

            vals = {
                'carrier': data.get('CarrierName', ""),
                'errors': "\n".join(data.get('Errors', [])) or "",
                'notifications': "\n".join(data.get('Notifications', [])) or "",
                'tracking_url': data.get('Consignments', [{}])[0].get('TrackingUrl', ''),
                'consignment_nr': data.get('Consignments', [{}])[0].get('Connote', '')
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
            for event in data.get('Events'):
                event_date = datetime.strptime(event.get('EventDT', ""), "%Y-%m-%dT%H:%M:%S.%f")
                event_date = fields.Datetime.to_string(event_date)
                item = {
                    'date': event_date,
                    'description': event.get('Description') or "",
                    'location': event.get('Location') or "",
                    'part': event.get('Part') or ""
                }
                events.append(item)

            vals = {
                'delivery_status': data.get('Status') or 'Unknown',
                'delivery_date': data.get('Delivered') or "",
                'delivery_events': ""
            }

            if events:
                template = Template(EVENTS_TEMPLATE)
                res = template.render({'events': events})
                vals['delivery_events'] = res

            line.update(vals)

    ###########################################################################
    # Fields
    ###########################################################################
    return_shipment = fields.Many2one(_name, "Return Shipment", readonly=True, ondelete='set null')
    is_return_for = fields.Many2one(comodel_name=_name)

    ###########################################################################
    # Model methods
    ###########################################################################
    @staticmethod
    def _is_dev_mode():
        return configuration.get(CONFIG_SECTION, "dev_mode", fallback="0")

    @api.model
    def _get_api_config(self, picking):
        api_key = CONFIG['headers'].get('ACCESS_KEY')
        email_id = CONFIG['headers'].get('SUPPORT_EMAIL')
        # If support email or api key are set as dictionaries, extract the values based on the current company ID.
        # If value is not stored as dictionary, this will fail on eval, and use the original values.
        try:
            company_id = self.env.company.id

            api_key_dict = eval(api_key)
            access_key = api_key_dict.get(company_id)
            if access_key:
                CONFIG['headers']['ACCESS_KEY'] = access_key

            email_dict = eval(email_id)
            email = email_dict.get(company_id)
            if email:
                CONFIG['headers']['SUPPORT_EMAIL'] = email
        except:
            pass

        return CONFIG

    @api.model
    def _get_recipient_name(self, picking):
        partner = picking.partner_id
        return (partner.parent_id.name or partner.name or "")[:50]  # 50 chars is maximum supported by GSS

    @api.model
    def create_shipment(self, ship_wizard):

        picking = ship_wizard.picking_id
        carrier_service = ship_wizard.service_id

        ref = picking.name

        order = CarrierShipment()
        order.DeliveryReference = "*TEST({})".format(ref) if self._is_dev_mode() else ref
        order.Carrier = carrier_service.carrier_name
        order.Service = carrier_service.carrier_service
        order.QuoteId = carrier_service.quote_id
        order.IsSaturdayDelivery = ship_wizard.is_saturday_delivery
        order.IsSignatureRequired = ship_wizard.is_signature_required

        if ship_wizard.is_dangerous_goods:
            self.append_dangerous_goods(order=order, ship_wizard=ship_wizard)

        if not self._is_dev_mode():
            order.PrintToPrinter = 'true' if picking.carrier_id.gss_print_via_agent else 'false'

        partner = picking.partner_id

        dest = order.Destination

        dest.Name = self._get_recipient_name(picking)
        dest.ContactPerson = partner.name or ""
        dest.PhoneNumber = partner.phone or ""
        dest.DeliveryInstructions = ship_wizard.delivery_instructions or ""
        dest.Email = partner.email or ""
        if dest.Email:
            dest.SendTrackingEmail = True

        address = dest.Address
        if ship_wizard.alternate_address:
            pseudo_partner = ship_wizard.make_alternate_address_pseudo_partner()
            self._build_delivery_address(pseudo_partner, address)
        else:
            self._build_delivery_address(partner, address)

        if self._is_dev_mode():
            dest.Name = "*TEST({})".format(dest.Name[:43])  # since we're adding 7 extra chars, reduce the name to 43

        total_weight = 0
        total_packages = 0
        for p in ship_wizard.detail_ids:
            total_packages += p.qty
            for _ in range(p.qty):
                if p.box_id.package_code:
                    package_code = p.box_id.package_code.name
                else:
                    package_code = None

                order.Packages.append(self.prepare_package_object(
                    name=p.box_id.name,
                    weight=p.weight,
                    length=p.box_id.length,
                    width=p.box_id.width,
                    height=p.box_id.height,
                    package_type=p.box_id.type,
                    package_code=package_code,
                ))
                total_weight += p.weight

        self.include_extra_packages(ship_wizard=ship_wizard, packages=order.Packages)

        response = self.request_post(self._get_api_config(picking), ORDER_CONTEXT, order.to_json())
        if not response:
            return self

        CarrierShipment.validate_shipment_post_response(response)
        shipment = self.create(
            [{
                "picking_id": picking.id,
                "json_post": json.dumps(response),
                "shipping_cost": carrier_service.cost}
            ])
        self.attach_labels(shipment)

        picking_values = {
            'weight': total_weight,
            'shipping_weight': total_weight,
            'number_of_packages': total_packages
        }

        shipment._update_picking_fields(tracking_nrs=[shipment.consignment_nr], picking_values=picking_values)

        return shipment

    def attach_labels(self, shipment):
        """
        Get labels and attach to the shipment on ir.attachment.

        :param shipment: gss.carrier.shipment
        """
        for label in shipment.get_print_label_documents():
            name, label_data, doc_type = label
            if doc_type == PDF_OUTPUT_TYPE:
                mimetype = MIMETYPE_PDF
                suffix = "pdf"
                datas = base64.b64encode(base64.b64decode(label_data))

            elif doc_type == PNG_OUTPUT_TYPE:
                mimetype = MIMETYPE_PNG
                suffix = "png"

                # GSS' image needs to re-oriented to mirror the PDF
                image = Image.open(io.BytesIO(base64.b64decode(label_data)))
                rotated = image.rotate(-90, expand=True)

                out = io.BytesIO()
                rotated.save(out, format="png")
                datas = base64.b64encode(out.getvalue())

            else:
                # Catchall
                mimetype = MIMETYPE_BIN
                suffix = "bin"
                datas = base64.b64encode(base64.b64decode(label_data))

            self.env["ir.attachment"].sudo().create(
                [{
                    "datas": datas,
                    "name": f"{name}.{suffix}",
                    "mimetype": mimetype,
                    "res_id": shipment.id,
                    "res_model": shipment._name
                }])

    @api.model
    def append_dangerous_goods(self, order, ship_wizard):
        order.HasDG = ship_wizard.is_dangerous_goods

        items = []

        for good in ship_wizard.dangerous_goods_ids:
            items.append({
                "ConsignmentId": 0,
                "Description": good.shipping_name or "",
                "ClassOrDivision": good.shipping_class or "",
                "UNorIDNo": good.un_or_id or "",
                "PackingGroup": good.packing_group or "",
                "SubsidaryRisk": good.subsidiary_risk or "",
                "Packing": good.packing_qty_type or "",
                "PackingInstr": good.packing_instructions or "",
                "Authorization": good.authorization or "Storeperson"
            })

        if not items:
            items = [{
                "ConsignmentId": 0,
                "Description": "",
                "ClassOrDivision": "",
                "UNorIDNo": "",
                "PackingGroup": "",
                "SubsidaryRisk": "",
                "Packing": "",
                "PackingInstr": "",
                "Authorization": "Storeperson"
            }]

        order.DangerousGoods = {
            "AdditionalHandlingInfo": ship_wizard.handling_info or "",
            "HazchemCode": ship_wizard.hazchem_code or "",
            "IsRadioActive": ship_wizard.carrier.gss_dg_radioactive_preset or False,
            "CargoAircraftOnly": ship_wizard.carrier.gss_dg_cargo_aircraft_only_preset or False,
            "IsRoadTransport": ship_wizard.carrier.gss_dg_road_transport_preset or False,
            "LineItems": items,
            "TotalQuantity": ship_wizard.total_qty,
            "TotalKg": ship_wizard.total_kg,
        }

    @api.model
    def create_return_shipment(self, outbound_shipment, ship_wizard):
        picking = outbound_shipment.picking_id
        carrier_service = ship_wizard.service_id

        ref = "RET/{}".format(picking.name)

        order = InboundCarrierShipment()
        order.DeliveryReference = "*TEST({})".format(ref) if self._is_dev_mode() else ref
        order.Carrier = carrier_service.carrier_name
        order.IsSaturdayDelivery = ship_wizard.is_saturday_delivery
        order.IsSignatureRequired = ship_wizard.is_signature_required
        origin_partner = picking.partner_id
        if not self._is_dev_mode():
            order.PrintToPrinter = 'true' if picking.carrier_id.gss_print_via_agent else 'false'
        dest_partner = self._get_addr(picking.company_id.partner_id, 'delivery')

        origin = order.Origin
        origin.Name = origin_partner.parent_id.name or origin_partner.name
        origin.ContactPerson = origin_partner.name or ""
        origin.PhoneNumber = origin_partner.phone or ""
        origin.DeliveryInstructions = ""
        origin.Email = origin_partner.email or ""

        address = origin.Address
        if ship_wizard.alternate_address:
            pseudo_partner = ship_wizard.make_alternate_address_pseudo_partner()
            self._build_delivery_address(pseudo_partner, address)
        else:
            self._build_delivery_address(origin_partner, address)

        if self._is_dev_mode():
            origin.Name = "*TEST({})".format(origin.Name)

        dest = order.Destination
        dest.Name = dest_partner.parent_id.name or dest_partner.name
        dest.ContactPerson = dest_partner.name or ""
        dest.PhoneNumber = dest_partner.phone or ""
        dest.DeliveryInstructions = ""
        dest.Email = dest_partner.email or ""
        if dest.Email:
            dest.SendTrackingEmail = True

        address = dest.Address
        self._build_delivery_address(dest_partner, address)
        if self._is_dev_mode():
            dest.Name = "*TEST({})".format(dest.Name)

        for p in ship_wizard.detail_ids:
            for _ in range(p.qty):
                if p.box_id.package_code:
                    package_code = p.box_id.package_code.name
                else:
                    package_code = None

                order.Packages.append(self.prepare_package_object(
                    name=p.box_id.name,
                    weight=p.weight,
                    length=p.box_id.length,
                    width=p.box_id.width,
                    height=p.box_id.height,
                    package_type=p.box_id.type,
                    package_code=package_code,
                ))

        self.include_extra_packages(ship_wizard=ship_wizard, packages=order.Packages)

        response = self.request_post(self._get_api_config(picking), ORDER_CONTEXT, order.to_json())
        if not response:
            return self

        InboundCarrierShipment.validate_shipment_post_response(response)
        shipment = self.create(
            [{
                "picking_id": picking.id,
                "json_post": json.dumps(response),
            }])
        self.attach_labels(shipment)
        outbound_shipment.return_shipment = shipment.id

        return shipment

    @api.model
    def _build_delivery_address(self, partner, address):
        """
        :param partner: res.partner
        :param address: GSS-API Address
        :return:
        """
        address.BuildingName = partner.building or ""
        address.StreetAddress = partner.street or ""
        address.Suburb = partner.street2 or ""
        address.City = partner.city or ""
        address.Postcode = partner.zip or ""
        address.CountryCode = (partner.country_id.code or partner.company_id.partner_id.country_id.code or "NZ").upper()

    @api.model
    def get_available_services(self, ship_wizard):
        ship_model = self.env['gss.carrier.shipment']

        ref = ship_wizard.picking_id.name
        partner = ship_model._get_addr(ship_wizard.picking_id.partner_id, 'delivery')

        rates = ServiceRates()
        rates.DeliveryReference = ref
        rates.IsSaturdayDelivery = ship_wizard.is_saturday_delivery
        rates.IsSignatureRequired = ship_wizard.is_signature_required

        dest = rates.Destination

        dest.Name = partner.parent_id.name or partner.name
        dest.ContactPerson = partner.name or ""
        dest.PhoneNumber = partner.phone or ""
        dest.Email = partner.email or ""

        address = dest.Address

        if ship_wizard.alternate_address:
            pseudo_partner = ship_wizard.make_alternate_address_pseudo_partner()
            ship_model._build_delivery_address(pseudo_partner, address)
        else:
            ship_model._build_delivery_address(partner, address)

        # Prepare package details
        self.add_packages(ship_wizard=ship_wizard, rates=rates)

        response = self.request_post(self._get_api_config(ship_wizard.picking_id), RATES_CONTEXT, rates.to_json())
        if not response:
            raise UserError("No or invalid response from GSS")

        ServiceRates.validate_rates_post_response(response)
        records = self._create_services_from_response(response, ship_wizard)

        return records

    @api.model
    def include_extra_packages(self, ship_wizard, packages):
        """Extend with extra stuff in inheriting modules"""
        if ship_wizard.custom_boxes:
            for box in ship_wizard.custom_box_ids:
                packages.append(self.prepare_package_object(
                    name=box.package_name,
                    weight=box.weight,
                    length=box.length,
                    width=box.width,
                    height=box.height
                ))

    @api.model
    def add_packages(self, ship_wizard, rates):
        for p in ship_wizard.detail_ids:
            for _ in range(p.qty):
                if p.box_id.package_code:
                    package_code = p.box_id.package_code.name
                else:
                    package_code = None

                rates.Packages.append(self.prepare_package_object(
                    name=p.box_id.name,
                    weight=p.weight,
                    length=p.box_id.length,
                    width=p.box_id.width,
                    height=p.box_id.height,
                    package_type=p.box_id.type,
                    package_code=package_code,
                ))

        if ship_wizard.custom_boxes:
            for box in ship_wizard.custom_box_ids:
                rates.Packages.append(self.prepare_package_object(
                    name=box.package_name,
                    weight=box.weight,
                    length=box.length,
                    width=box.width,
                    height=box.height
                ))

    @api.model
    def prepare_package_object(self, name, weight, length, width, height, package_type=None, package_code=None):
        package = Package()
        package.Kg = weight
        package.Length = length
        package.Width = width
        package.Height = height
        package.Type = package_type
        package.PackageCode = package_code
        package.Name = name
        return package

    @api.model
    def _create_services_from_response(self, response, ship_wizard):
        available = response.get('Available')
        vals_list = []

        def _sanitize(text: str):
            return text.strip('\r\n ')

        if not available:
            return self.browse()  # Empty record set
        for service in available:
            vals = {'ship_wizard': ship_wizard.id,
                    'services_request_iteration': ship_wizard.services_request_iteration,
                    'quote_id': service.get('QuoteId', ''),
                    'carrier_name': _sanitize(service.get('CarrierName', '')),
                    'carrier_service': _sanitize(service.get('ServiceStandard', '')),
                    'delivery_type': _sanitize(service.get('DeliveryType', '')),
                    'cost': service.get('Cost', 0)
                    }
            vals_list.append(vals)

        if vals_list:
            return self.env['delivery.carrier.service'].create(vals_list)

    def get_print_label_documents(self):
        self.ensure_one()

        if not self.json_post:
            return None

        data = json.loads(self.json_post)
        res = []
        consignments = data.get('Consignments')
        for consignment in consignments:
            name = consignment.get('Connote', 'document')
            files = consignment.get('OutputFiles')
            for doc_type, doc_data in files.items():
                for doc in doc_data:
                    res.append((name, doc, doc_type))

        return res

    def update_shipment(self):
        self.ensure_one()

        if not self.consignment_nr:
            raise UserError("Shipment has no consignment number")

        response = self.request_get(self._get_api_config(self.picking_id),
                                    ORDER_CONTEXT,
                                    {'shipments': self.consignment_nr})

        CarrierShipment.validate_shipment_get_response(response)

        results = response.get("Results")
        if not results:
            return False

        result = results[0]

        if not self.picking_id.cubic_measure:
            self.picking_id.cubic_measure = result.get('TotalCubic')

        self.json_get = json.dumps(result)
        self.last_updated = fields.Datetime.now()

        return True
