# -*- coding: utf-8 -*-
import base64
import logging
from io import BytesIO

from PyPDF2 import PdfFileMerger

from odoo import models, fields, api
from odoo.exceptions import UserError
from .label_printer import MIMETYPE_PDF

_logger = logging.getLogger(__name__)


class CarrierShipmentAbstract(models.AbstractModel):
    _name = "carrier.shipment.abstract"
    _description = "Carrier Shipment Base Model"

    ###########################################################################
    # Default & compute methods
    ###########################################################################
    @api.depends('json_post')
    def _compute_all(self):
        """
        The idea is to save the response form the POST to DB (json_post) then read values from the response.
        Returns: None
        """
        raise NotImplementedError

    @api.depends('json_get')
    def _compute_delivery_status(self):
        """
        The idea is to save the GET response to DB (json_get) then read values from the response.
        Returns: None
        """
        raise NotImplementedError

    def _compute_is_return(self):
        for rec in self:
            parent_rec = self.search([('return_shipment', '=', rec.id)])
            if parent_rec:
                rec.is_return_for = parent_rec
            else:
                rec.is_return_for = False

    def _get_labels_as_pdf(self):
        for rec in self:
            attachments = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", rec.id),
                    ("mimetype", "=", MIMETYPE_PDF),
                ])
            if not attachments:
                rec.pdf_labels = None
                rec.pdf_labels_file_name = False
                continue
            if rec.return_shipment:
                return_shipment = rec.return_shipment
                attachments += self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", self._name),
                        ("res_id", "=", return_shipment.id),
                        ("mimetype", "=", MIMETYPE_PDF),
                    ])

            merger = PdfFileMerger()
            for attachment in attachments:
                merger.append(BytesIO(base64.b64decode(attachment.datas)))
            merged = BytesIO()
            merger.write(merged)
            rec.pdf_labels = base64.encodebytes(merged.getvalue())
            rec.pdf_labels_file_name = 'shipping_labels.pdf'

    ###########################################################################
    # Fields
    ###########################################################################
    json_post = fields.Text("JSON POST Response", readonly=True)
    json_get = fields.Text("JSON GET Response", readonly=True)

    picking_id = fields.Many2one("stock.picking", string="Picking", readonly=True)
    order_number = fields.Char("Order Number", related="picking_id.name", readonly=True)
    # NOTE: You have to re-define these two fields in your model, as _name is the abstract model in this file
    return_shipment = fields.Many2one(_name, "Return Shipment", readonly=True, ondelete='set null')
    is_return_for = fields.Many2one(comodel_name=_name, compute='_compute_is_return')
    return_shipment_failed = fields.Text(readonly=True, help="Error message from request of the return shipment")

    consignment_nr = fields.Char("Consignment Number", compute="_compute_all")
    carrier = fields.Char("Carrier", compute="_compute_all")
    tracking_url = fields.Char("Tracking URL", compute="_compute_all")
    errors = fields.Text("Errors", compute='_compute_all')
    notifications = fields.Text("Notifications", compute='_compute_all')

    delivery_status = fields.Char("Status", compute='_compute_delivery_status', readonly=True)
    delivery_date = fields.Char("Delivery Date", compute='_compute_delivery_status', readonly=True)
    delivery_events = fields.Text("Events", compute='_compute_delivery_status', readonly=True)
    last_updated = fields.Datetime("Last updated", readonly=True, default=fields.Datetime.now)

    printer_id = fields.Many2one("carrier.label.printer", "Label Printer")

    pdf_labels = fields.Binary(compute='_get_labels_as_pdf')
    pdf_labels_file_name = fields.Char(compute='_get_labels_as_pdf')
    shipping_cost = fields.Float("GSS Shipping Cost", readonly=True)

    ###########################################################################
    # Model methods
    ###########################################################################

    @api.depends('order_number', 'consignment_nr')
    def _compute_display_name(self):
        for record in self:
            if record.order_number and record.consignment_nr:
                record.display_name = f"{record.order_number}:{record.consignment_nr}"
            else:
                record.display_name = ""

    def _update_picking_fields(self, tracking_nrs=None, picking_values=None):
        tracking_nrs = tracking_nrs or []
        picking_values = picking_values or []

        if tracking_nrs:
            vals = {'carrier_tracking_ref': ','.join(tracking_nrs)}
            self.picking_id.write(vals)

        if picking_values:
            self.picking_id.write(picking_values)

        return True

    @api.model
    def create_shipment(self, ship_wizard):
        """
        Called by the wizard to place the shipment at carrier via API
        Args:
            ship_wizard: Shipping wizard browse record

        Returns:

        """
        raise NotImplementedError

    @api.model
    def create_return_shipment(self, outbound_shipment, ship_wizard):
        """
        Called by the wizard to place a return shipment after the outbound shipment has been done.
        Args:
            outbound_shipment: browse record of outbound shipment
            ship_wizard: Shipping wizard browse record

        Returns:

        """

    def action_refresh(self):
        """
        Button action to update shipping information. Must implement update_shipment.
        Returns:

        """
        self.update_shipment()

    def update_shipment(self):
        """
        Method called to get status update of shipping
        Returns:

        """
        raise NotImplementedError

    def action_reprint_labels(self):
        """
        Reprints the attached PDF labels
        Returns: None

        """
        self.ensure_one()

        attachments = self.env['ir.attachment'].search([('res_id', '=', self.id),
                                                        ('res_model', '=', self._name)])
        if not attachments:
            raise UserError("No labels to print")
        if not self.printer_id:
            raise UserError("Please select a printer")

        for attachment in attachments:
            self.printer_id.print_attachment(attachment, raise_exceptions=True)

    def download_attached_labels(self):
        self.ensure_one()
        file = self.pdf_labels
        if not file:
            raise UserError("No labels to download")
        return {
            'name': 'Download labels',
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={model}&id={id}&field=pdf_labels&filename_field=pdf_labels_file_name&download=true'.format(
                id=self.id,
                model=self._name
            ),
            'target': 'self'
        }

    @api.model
    def _get_addr(self, partner, addr_type):
        """
        @return: a res.partner browse record of partner and type
        @param partner: usually latest partner browse record - 'o'
        @param addr_type: the type of address e.g. 'invoice'
        """
        addresses = partner.address_get([addr_type])
        if addresses and addresses[addr_type]:
            partner_model = self.env["res.partner"]
            res_partner_address = partner_model.browse([addresses[addr_type]])
            return res_partner_address[0]

        # default to the base record
        return partner

    @api.model
    def view_address_sample(self, partner):
        """
        Simple Validation tests.

        :param partner:
        :return:
        """
        res = []
        if partner.building:
            res.append(partner.building)

        res.append(partner.street or "*MISSING STREET")
        if partner.street2:
            res.append(partner.street2)

        if partner.city and partner.zip:
            res.append("{},{}".format(partner.city, partner.zip))
        else:
            if partner.city:
                res.append("{}, *MISSING POST CODE".format(partner.city))
            else:
                res.append("*MISSING CITY, {}".format(partner.zip))

        if partner.country_id:
            res.append(partner.country_id.code)

        sampled = '\n'.join(res)
        valid = '*MISSING' not in sampled
        return valid, sampled

    @api.model
    def _build_delivery_address(self, partner, address):
        country_code = partner.country_id.code or 'NZ'
        address.BuildingName = (partner.building and partner.building[:50]) or ""
        address.StreetAddress = partner.street or ""
        address.Suburb = partner.street2 or ""
        address.City = partner.city or ""
        address.Postcode = partner.zip or ""
        address.CountryCode = country_code.upper() or ""
