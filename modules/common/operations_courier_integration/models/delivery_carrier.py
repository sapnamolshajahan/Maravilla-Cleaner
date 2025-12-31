# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ################################################################################
    # Fields
    ################################################################################
    ship_after_validation = fields.Boolean('Ship as separate step', default=True)

    price_unit_rounding_digits = fields.Float(
        default=0.0,
        digits=(10, 4),
        help="Courier freight charges will be rounded to this many digits.  Use 0.10 for nearest 10 cents.  "
        + "Set to zero to disable rounding.",
    )

    ################################################################################
    # Methods
    ################################################################################

    def get_carrier_shipment_model(self, delivery_carrier):
        """
        This method is called by the shipment wizard to get the carrier shipment model
        Override and return your carrier shipment model(one that inherits from carrier.shipment.abstract). If
        the delivery_carrier is not associated with your carrier shipment model then return super
        if delivery_carrier.delivery_type == 'ABC':
            return 'ABC.carrier.shipment'
        else:
            return super...
        Args:
            delivery_carrier: delivery.carrier browse record

        Returns: the model (self.env['model'])

        """
        return

    @api.model
    def fixed_get_tracking_link(self, picking):
        res = super(DeliveryCarrier, self).fixed_get_tracking_link(picking)

        if not res:
            res = (picking.carrier_shipment and picking.carrier_shipment.tracking_url) or False

        return res

    def get_tracking_link(self, picking):
        if picking.carrier_shipment:
            return picking.carrier_shipment.tracking_url
        return super(DeliveryCarrier, self).get_tracking_link(picking)

    @api.model
    def _set_invoice_policy(self, vals):
        if "delivery_type" in vals:
            enabled = vals.get("delivery_type") not in ["fixed", "base_on_rule", False]
            if enabled:
                vals["invoice_policy"] = "real"
                vals["integration_level"] = "rate_and_ship"
            else:
                vals["invoice_policy"] = "estimated"

    def write(self, vals):
        self._set_invoice_policy(vals)
        return super(DeliveryCarrier, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._set_invoice_policy(vals)
        return super(DeliveryCarrier, self).create(vals_list)

    def send_shipping(self, picking):
        """
        STD Odoo function called to send shipping. Because the shipment is sent via the Wizard, the cost is calculated
        by the wizard and then written to picking.carrier_price. The shipment is actually sent after the picking is
        processed but still in the same transaction
        Args:
            picking: browse record of picking being confirmed

        Returns: list of dicts
        """
        if picking.carrier_id.delivery_type in ["fixed", "base_on_rule", False]:
            return super(DeliveryCarrier, self).send_shipping(picking)

        tracking_nr = picking.carrier_tracking_ref or "--> Check Shipment tab"
        vals = {"exact_price": picking.carrier_price, "tracking_number": tracking_nr}
        return [vals]
