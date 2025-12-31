# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError
from .sale_order import CONTEXT_SALE_LINE_PRICE_ROUNDING


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    def _compute_shipment_details(self):
        for rec in self:
            carrier_shipment_tracking_url = False
            carrier_shipping_cost = False
            if rec.carrier_shipment:
                carrier_shipment_tracking_url = rec.carrier_shipment.tracking_url
                carrier_shipping_cost = rec.carrier_shipment.shipping_cost

            rec.update({
                'carrier_shipment_tracking_url': carrier_shipment_tracking_url,
                'carrier_shipping_cost': carrier_shipping_cost
            })

    def _compute_carrier_integration(self):
        for rec in self:
            if rec.carrier_id.delivery_type not in ["fixed", "base_on_rule", False]:
                rec.has_carrier_integration = True
            else:
                rec.has_carrier_integration = False

    ################################################################################
    # Fields
    ################################################################################
    carrier_shipment = fields.Reference(selection=[], string="Shipment", readonly=True, copy=False)
    carrier_shipment_tracking_url = fields.Char("Tracking URL", compute="_compute_shipment_details", readonly=True)
    carrier_shipping_cost = fields.Float("Shipping Cost", compute="_compute_shipment_details", readonly=True)
    has_carrier_integration = fields.Boolean("Has Carrier Integration", compute="_compute_carrier_integration")
    ship_after_validation = fields.Boolean(related='carrier_id.ship_after_validation')
    carrier_price = fields.Float(copy=False)

    ################################################################################
    # Methods
    ################################################################################

    def button_download_courier_labels(self):
        self.ensure_one()
        if not self.carrier_shipment:
            raise UserError("No carrier shipment linked to picking")
        file = self.carrier_shipment.pdf_labels
        if not file:
            raise UserError("No labels to print")
        return {
            "name": "Download labels",
            "type": "ir.actions.act_url",
            "url": "/web/content/?model={model}&id={id}&field=pdf_labels&filename_field=pdf_labels_file_name&download=true".format(
                id=self.carrier_shipment.id, model=self.carrier_shipment._name
            ),
            "target": "self",
        }

    def action_validate_and_ship(self):
        self.ensure_one()

        if self.picking_type_id.code != "outgoing":
            raise UserError("Can only place shipments for outgoing pickings")

        wizard = self.env["carrier.shipment.wizard"].build(self)
        return {
            "type": "ir.actions.act_window",
            "name": wizard._description,
            "res_model": wizard._name,
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def action_ship_only(self):
        self.ensure_one()

        if self.picking_type_id.code != "outgoing":
            raise UserError("Can only place shipments for outgoing pickings")

        wizard = self.env["carrier.shipment.wizard"].build(self, is_ship_only=True)
        return {
            "type": "ir.actions.act_window",
            "name": wizard._description,
            "res_model": wizard._name,
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def send_to_shipper(self):
        """
        If no cost, then bypass the whole send_shipping and SO line update.
        """
        if self.carrier_id.delivery_type not in ["fixed", "base_on_rule", False] and not self.carrier_price:
            return

        super(StockPicking, self).send_to_shipper()

    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        ctx = dict(self.env.context)
        ctx[CONTEXT_SALE_LINE_PRICE_ROUNDING] = self.carrier_id.price_unit_rounding_digits
        return super(StockPicking, self.with_context(ctx))._add_delivery_cost_to_so()

    def button_reprint_courier_labels(self):
        """Reprint courier labels"""
        self.ensure_one()
        if not self.carrier_shipment:
            raise UserError("This delivery does not have a Carrier Shipment attached")

        self.carrier_shipment.action_reprint_labels()
        return True
