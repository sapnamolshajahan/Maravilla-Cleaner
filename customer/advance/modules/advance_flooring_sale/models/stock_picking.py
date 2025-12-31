from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    is_firm = fields.Boolean(string="Firm", related='sale_id.is_firm', store=True)
    is_commercial = fields.Boolean(string="Commercial", related='sale_id.is_commercial', store=True)

    def button_validate(self):
        for picking in self:
            if picking.is_commercial:
                if picking.sale_id:
                    sale_date = picking.sale_id.date_order.date()
                    scheduled_date = picking.scheduled_date.date()
                    if sale_date != scheduled_date:
                        raise ValidationError(_(
                            "The Scheduled Date (%s) doesn't match the Sale Order Date (%s)."
                        ) % (scheduled_date, sale_date))

            for line in picking.move_line_ids:
                # Only check LOT-tracked products
                if line.product_id.tracking != 'lot':
                    continue

                if not line.lot_id:
                    continue

                # Check available quantity for this LOT in this LOCATION
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('lot_id', '=', line.lot_id.id),
                    ('location_id', '=', line.location_id.id),
                ], limit=1)

                available_qty = quant.quantity if quant else 0

                # If user tries to consume more than available stock → BLOCK
                if line.quantity > available_qty:
                    raise UserError(_(
                        "You cannot validate this transfer.\n\n"
                        "LOT: %s\n"
                        "Requested Qty: %s\n"
                        "Available Qty in this LOT: %s\n\n"
                        "Please reduce the quantity or select another LOT."
                    ) % (line.lot_id.name, line.quantity, available_qty))

            if picking.is_firm and not self.env.context.get('confirm_validate'):
                return {
                    'name': _('Confirm Delivery'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking.confirm.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_picking_id': picking.id},
                }
        return super(StockPickingInherit, self).button_validate()

