from odoo import models, fields

class StockPickingConfirmWizard(models.TransientModel):
    _name = 'stock.picking.confirm.wizard'
    _description = 'Confirm Delivery Validation'

    picking_id = fields.Many2one('stock.picking', string="Picking", required=True)

    def action_confirm_picking(self):
        self.ensure_one()
        return self.picking_id.with_context(confirm_validate=True).button_validate()

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
