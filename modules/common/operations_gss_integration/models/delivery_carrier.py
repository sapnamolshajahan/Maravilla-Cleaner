# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"
    #################################################################################
    # Default & Compute methods
    #################################################################################

    #################################################################################
    # Fields
    #################################################################################
    delivery_type = fields.Selection(selection_add=[
        ('gss', 'Go Sweet Spot'),
    ], ondelete={"gss": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})})

    gss_print_via_agent = fields.Boolean("Send labels to print agent")

    # Dangerous Goods stuff
    gss_dg_hazchem_code_preset = fields.Char("Hazchem Code")
    gss_dg_cargo_aircraft_only_preset = fields.Boolean("Is Cargo Aircraft Only")
    gss_dg_road_transport_preset = fields.Boolean("Is Road Transport", default=True)
    gss_dg_radioactive_preset = fields.Boolean("Is RadioActive")
    gss_dg_additional_handling_info_preset = fields.Char("Additional Handling Info")

    #################################################################################
    # Methods
    #################################################################################
    def get_carrier_shipment_model(self, delivery_carrier):
        if delivery_carrier.delivery_type == 'gss':
            return self.env['gss.carrier.shipment']
        return super(DeliveryCarrier, self).get_carrier_shipment_model(delivery_carrier)

    def gss_rate_shipment(self, order):
        """
        Determine the cost of the shipment using GSS.
        Nope. Not allowed.
        """
        raise UserError("GSS shipping calculation is only allowed from Dispatch")
