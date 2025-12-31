# -*- coding: utf-8 -*-

import logging

from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CarrierShipmentWizard(models.TransientModel):
    _name = "carrier.shipment.wizard"
    _description = "Carrier Shipment Wizard"
    _rec_name = "picking_id"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    def _compute_warehouse(self):
        move = self.picking_id.move_ids[0]
        self.warehouse_id = move.warehouse_id.id

    def _compute_alternate_address(self):
        for rec in self:
            alternate_addr = False
            if rec.picking_id.sale_id:
                if hasattr(rec.picking_id.sale_id, "alternate_shipping_address"):
                    alternate_addr = rec.picking_id.sale_id.alternate_shipping_address

            rec.alternate_address = alternate_addr or False

    @api.depends("services_request_iteration")
    def _show_service_section(self):
        for rec in self:
            count = self.env["delivery.carrier.service"].search_count([
                ("ship_wizard", "=", rec.id),
                ("services_request_iteration", "=", self.services_request_iteration),
            ])
            rec.show_service_section = bool(count)

    @api.depends("carrier")
    def _has_carrier_integration(self):
        for rec in self:
            if rec.carrier:
                rec.has_carrier_integration = rec.carrier.delivery_type not in ("fixed", "base_on_rule")
            else:
                rec.has_carrier_integration = False

    ################################################################################
    # Fields
    ################################################################################

    self_id = fields.Integer(related="id", help="Technical field used in views")
    picking_id = fields.Many2one("stock.picking", "Picking", readonly=True, required=True, ondelete="cascade")
    carrier = fields.Many2one("delivery.carrier", ondelete="cascade")
    has_carrier_integration = fields.Boolean("Has Carrier Integration", compute="_has_carrier_integration")
    service_id = fields.Many2one("delivery.carrier.service", string="Service")
    detail_ids = fields.One2many("carrier.shipment.package", "wizard_id", "Packages")
    printer_id = fields.Many2one("carrier.label.printer", string="Printers")
    warehouse_id = fields.Many2one("stock.warehouse", compute="_compute_warehouse", string="Warehouse")
    services_request_iteration = fields.Integer("Services Request Iteration", default=0)
    is_saturday_delivery = fields.Boolean("Saturday Delivery?")
    is_signature_required = fields.Boolean("Signature?")
    is_dangerous_goods = fields.Boolean("Dangerous Goods?")
    return_label = fields.Boolean("Include Return Label")
    show_services_button = fields.Boolean("Show button", default=False)
    show_service_section = fields.Boolean("Show Service Section", compute="_show_service_section")
    delivery_instructions = fields.Char("Delivery Instructions", size=120)
    show_address = fields.Boolean("Show Address")
    alternate_address = fields.Text("Alternate Shipping Address", compute="_compute_alternate_address")

    building = fields.Char(related="picking_id.partner_id.building", readonly=False, related_sudo=True)
    street = fields.Char(related="picking_id.partner_id.street", readonly=False, related_sudo=True)
    street2 = fields.Char(related="picking_id.partner_id.street2", readonly=False, related_sudo=True)
    city = fields.Char(related="picking_id.partner_id.city", readonly=False, related_sudo=True)
    state_id = fields.Many2one(
        "res.country.state", related="picking_id.partner_id.state_id", readonly=False, related_sudo=True
    )
    zip = fields.Char(related="picking_id.partner_id.zip", readonly=False, related_sudo=True)
    country_id = fields.Many2one(
        "res.country", related="picking_id.partner_id.country_id", readonly=False, related_sudo=True
    )

    alt_building = fields.Char(related="picking_id.sale_id.alt_building", readonly=False, related_sudo=True)
    alt_street = fields.Char(related="picking_id.sale_id.alt_street", readonly=False, related_sudo=True)
    alt_street2 = fields.Char(related="picking_id.sale_id.alt_street2", readonly=False, related_sudo=True)
    alt_city = fields.Char(related="picking_id.sale_id.alt_city", readonly=False, related_sudo=True)
    alt_state_id = fields.Many2one(
        "res.country.state", related="picking_id.sale_id.alt_state_id", readonly=False, related_sudo=True
    )
    alt_zip = fields.Char(related="picking_id.sale_id.alt_zip", readonly=False, related_sudo=True)
    alt_country_id = fields.Many2one(
        "res.country", related="picking_id.sale_id.alt_country_id", readonly=False, related_sudo=True
    )
    pallet_id = fields.Many2one("stock.warehouse.box", "Pallets", domain="[('is_pallet', '=', True)]")
    pallet_qty = fields.Integer('Pallet QTY')
    is_ship_only = fields.Boolean('Ship Only?')
    shipment_model = fields.Char(string='Shipment Model')

    ################################################################################
    # Methods
    ################################################################################
    @api.model
    def build(self, picking, is_ship_only=False):
        """
        :param picking: stock.picking record
        :param is_ship_only: boolean
        :return:
        """
        if picking.carrier_shipment:
            raise UserError("Picking already has Shipment")

        values = {
            "picking_id": picking.id,
            "carrier": picking.carrier_id.id,
            "is_ship_only": is_ship_only,
        }

        # Default printer
        warehouse = picking.move_line_ids[0].location_id.warehouse_id if picking.move_line_ids else None
        default_printer = None
        if warehouse:
            for label_printer in warehouse.carrier_label_printer_ids:
                if label_printer.default:
                    default_printer = label_printer
                    break

        values["printer_id"] = default_printer.id if default_printer else None
        wizard = self.create([values])

        if wizard.picking_id:
            partner = wizard.picking_id.partner_id

            if partner:
                wizard.write({
                    'building': partner.building,
                    'street': partner.street,
                    'street2': partner.street2,
                    'city': partner.city,
                    'zip': partner.zip,
                    'state_id': partner.state_id and partner.state_id.id,
                    'country_id': partner.country_id and partner.country_id.id,
                })

        return wizard

    def make_address_pseudo_partner(self):
        self.ensure_one()

        class dummy(object):
            pass

        partner = dummy()
        partner.building = self.building or ""
        partner.street = self.street or ""
        partner.street2 = self.street2 or ""
        partner.city = self.city or ""
        partner.state_id = self.state_id or self.env["res.country.state"].browse()
        partner.zip = self.zip or ""
        partner.country_id = self.country_id or self.env.company.country_id

        return partner

    def make_alternate_address_pseudo_partner(self):
        self.ensure_one()

        class dummy(object):
            pass

        partner = dummy()
        partner.building = self.alt_building or ""
        partner.street = self.alt_street or ""
        partner.street2 = self.alt_street2 or ""
        partner.city = self.alt_city or ""
        partner.state_id = self.alt_state_id or self.env["res.country.state"].browse()
        partner.zip = self.alt_zip or ""
        partner.country_id = self.alt_country_id or self.env.company.country_id

        return partner

    @api.onchange("detail_ids")
    def onchange_detail_ids(self):
        if len(self.detail_ids) > 0:
            self.show_services_button = True
        else:
            self.show_services_button = False

    def package_details_supplied(self):
        return bool(self.detail_ids)

    @api.onchange("is_saturday_delivery", "is_signature_required")
    def onchange_flags(self):
        if len(self.detail_ids) > 0:
            self.show_services_button = True

    def _validate_shipping_address(self):
        # Validate the address for the chosen carrier
        shipment_model = self.env["delivery.carrier"].get_carrier_shipment_model(self.carrier)
        address = self.make_address_pseudo_partner()

        if self.alternate_address:
            address = self.make_alternate_address_pseudo_partner()

        if not address.country_id:
            address.country_id = self.env.company.country_id

        valid, sample_addr = shipment_model.view_address_sample(address)

        if not valid:
            raise UserError(f"The shipping address is not valid:\n{sample_addr}\n\nPlease rectify address first.")

    def validate_before_getting_services(self):
        if not self.detail_ids:
            raise UserError("Package details are required.")

    def button_get_services(self):
        self.ensure_one()

        self.validate_before_getting_services()

        self._validate_shipping_address()
        self.services_request_iteration += 1
        self.show_services_button = False
        self.service_id = False

        shipment_model = self.env["delivery.carrier"].get_carrier_shipment_model(self.carrier)
        services = shipment_model.get_available_services(self)

        if not services:
            raise UserError("No carrier service available for destination address")

        return {
            "type": "ir.actions.act_window",
            "name": "Create Carrier Shipment",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def print_shipment_details(self, shipment):
        """

        :param shipment: delivery.carrier record
        :return:
        """
        printer = self.printer_id or self.warehouse_id.default_printer()
        if not printer:
            _logger.warning("carrier_label_printer_ids unspecified, label print ignored")
            return

        attachment_model = self.env["ir.attachment"]
        attachments = attachment_model.search(
            [
                ("res_id", "=", shipment.id),
                ("res_model", "=", shipment._name),
            ]
        )
        for attachment in attachments:
            printer.print_attachment(attachment)
        shipment.write({"printer_id": printer.id})

    def include_and_print_return_shipment(self, shipment, shipment_model):
        """
        Printer would have already been set on the main shipment
        If not set - ignore
        """
        return_shipment = False

        try:
            if self.return_label:
                return_shipment = shipment_model.create_return_shipment(shipment, self)

        except Exception as e:
            shipment.return_shipment_failed = str(e)

        # Print out return labels as well
        printer = self.printer_id or self.warehouse_id.default_printer()

        if not printer:
            return

        if self.warehouse_id.carrier_label_printer_ids and return_shipment:
            attachments = self.env['ir.attachment'].search([
                ('res_id', '=', return_shipment.id),
                ('res_model', '=', return_shipment._name)])

            for attachment in attachments:
                printer.print_attachment(attachment)

    def button_send_shipment(self):
        """
        Generate Shipment Details.
        """
        self.ensure_one()

        if not self.service_id:
            raise UserError("Value required for Service field.")
        self._validate_shipping_address()

        if float_utils.float_is_zero(self.carrier.price_unit_rounding_digits, precision_digits=4):
            carrier_price = self.service_id.cost
        else:
            carrier_price = float_utils.float_round(
                self.service_id.cost, precision_rounding=self.carrier.price_unit_rounding_digits)

        self.picking_id.write({
            "carrier_id": self.carrier.id,
            "carrier_price": carrier_price,
        })

        shipment_model = self.env["delivery.carrier"].get_carrier_shipment_model(self.carrier)

        # this will place the carrier shipment and create a carrier shipment object if successful
        shipment = shipment_model.create_shipment(self)
        if not shipment:
            raise UserError("Failed to create carrier shipment, view logs for details")

        self.picking_id.carrier_shipment = "{},{}".format(shipment._name, shipment.id)
        self.print_shipment_details(shipment)
        self.include_and_print_return_shipment(shipment, shipment_model)

        return self.return_base_form()

    def return_base_form(self):
        return {
            "name": "Form",
            "view_mode": "form",
            "res_model": 'stock.picking',
            "res_id": self.picking_id.id,
            "type": "ir.actions.act_window",
            "target": "main",
        }

    def button_cancel_shipment(self):
        return self.return_base_form()


class CarrierShipmentPackage(models.TransientModel):
    _name = "carrier.shipment.package"
    _description = "Shipment Wizard Package Line"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    @api.constrains("weight")
    def validate_weight(self):
        for line in self:
            if float_utils.float_compare(line.weight, 0.0, precision_digits=2) < 1:
                raise ValidationError("Package weight must be greater than 0 kgs")
        return True

    @api.constrains("qty")
    def validate_qty(self):
        for line in self:
            if float_utils.float_compare(line.qty, 0.0, precision_digits=2) < 1:
                raise ValidationError("Package Qty must be greater than 0")

        return True

    ###########################################################################
    # Fields
    ###########################################################################

    wizard_id = fields.Many2one("carrier.shipment.wizard", "Wizard", required=True, ondelete="cascade")
    box_id = fields.Many2one("stock.warehouse.box", "Box", required=True, domain=[("is_pallet", "=", False)])
    weight = fields.Float("Weight(kg)", default=1, required=True)
    qty = fields.Integer("Quantity", default=1, required=True)
    pallet_qty = fields.Integer("No. of Pallets", default=0)

    ###########################################################################
    # Model's methods
    ###########################################################################

    @api.onchange("box_id")
    def onchange_box(self):
        if self.box_id:
            self.weight = self.box_id.default_kgs
        else:
            self.weight = 1.0
