import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    edi_sent = fields.Datetime("EDI Sent At", readonly=True)
    carton_qty = fields.Integer(
        string="Number of Cartons",
        default=0,
        tracking=True,
    )
    pallet_qty = fields.Integer(
        string="Number of Pallets",
        default=0,
        tracking=True,
    )

    @api.constrains('carton_qty', 'pallet_qty')
    def _check_non_negative_counts(self):
        """Ensure values are not negative."""
        for rec in self:
            if rec.carton_qty < 0 or rec.pallet_qty < 0:
                raise ValidationError("Carton and Pallet quantities must be zero or positive.")

    def button_validate(self):
        for picking in self:
            partners_to_check = [picking.partner_id]
            if picking.sale_id and picking.sale_id.partner_id:
                partners_to_check.append(picking.sale_id.partner_id)

            # Trigger if any of them (or their parent) is Bunnings
            if any(p.is_bunnings_partner() for p in partners_to_check):
                if picking.carton_qty <= 0 and picking.pallet_qty <= 0:
                    raise ValidationError(
                        "For Bunnings deliveries, you must specify either "
                        "the Number of Cartons or the Number of Pallets."
                    )

        res = super().button_validate()

        for picking in self:
            partners_to_check = [picking.partner_id]
            if picking.sale_id and picking.sale_id.partner_id:
                partners_to_check.append(picking.sale_id.partner_id)

            if any(p.is_bunnings_partner() for p in partners_to_check):
                try:
                    customer = picking.partner_id
                    self.env["bunnings.edi"].send_edi(customer, picking, message_type="ASN")
                    _logger.info(
                        "EDI ASN sent for Picking %s (Partner %s, edi_reference=%s)",
                        picking.id,
                        customer.id,
                        customer.edi_reference or (customer.parent_id and customer.parent_id.edi_reference),
                    )
                except Exception as e:
                    _logger.exception(
                        "EDI ASN failed for Picking %s (Partner %s). Error: %s",
                        picking.id,
                        picking.partner_id.id,
                        str(e),
                    )
        return res
