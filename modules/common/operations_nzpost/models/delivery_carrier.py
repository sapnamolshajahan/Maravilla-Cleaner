from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[('eship', 'eShip(NZ Post)')],
        ondelete={"eship": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})})

    def get_carrier_shipment_model(self, delivery_carrier):
        if delivery_carrier.delivery_type == 'eship':
            return self.env['eship.carrier.shipment']
        return super(DeliveryCarrier, self).get_carrier_shipment_model(delivery_carrier)
