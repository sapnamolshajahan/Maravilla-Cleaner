from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrierService(models.TransientModel):

    _name = "delivery.carrier.service"
    _description = 'Delivery Carrier Service'

    def _compute_name(self):
        for rec in self:
            rec.name = "{name} ({type}) @ ${cost} - {service}".format(name=rec.carrier_name,
                                                                      type=rec.delivery_type,
                                                                      service=rec.carrier_service,
                                                                      cost=rec.cost)

    ship_wizard = fields.Many2one('carrier.shipment.wizard', 'Shipment Wizard', required=True, ondelete='cascade')
    services_request_iteration = fields.Integer("Services Request Iteration", required=True)
    quote_id = fields.Char('Quote ID', required=True)
    carrier_name = fields.Char('Description', required=True)
    carrier_service = fields.Char('Service', required=True)
    delivery_type = fields.Char('Delivery Type')
    cost = fields.Float('Cost')
    name = fields.Char("Name", compute='_compute_name')

    @api.depends('carrier_name', 'delivery_type', 'carrier_service', 'cost')
    def _compute_display_name(self):
        for record in self:
            if all([record.carrier_name, record.delivery_type, record.carrier_service, record.cost is not None]):
                record.display_name = f"{record.carrier_name} ({record.delivery_type}) @ ${record.cost} - {record.carrier_service}"
            else:
                record.display_name = ""

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        # TODO Got a feeling we need to override this to search for name as formatted in name_get
        return super(DeliveryCarrierService, self).name_search(name=name, args=args, operator=operator, limit=limit)
