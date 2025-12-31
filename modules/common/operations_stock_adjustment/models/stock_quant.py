from odoo import api, fields, models

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    operations_adjustment_reason = fields.Many2one('operations.adjustment.reason')
    state = fields.Selection([('waiting', 'Waiting Approval'), ('done', 'Done')])
    adjustment_value = fields.Float(compute='compute_adjustment_value', store=True)

    def request_approval(self):
        for rec in self:
            rec.state = 'waiting'
        mail_tmpl = self.env.ref('operations_stock_adjustment.ia_approval_mail_new')
        mail_tmpl.sudo().send_mail(self.env.company.id, force_send=False, raise_exception=True)

    def action_set_inventory_quantity_to_zero(self):
        res = super(StockQuant, self).action_set_inventory_quantity_to_zero()
        self.state = ''
        self.user_id = False
        return res

    @api.onchange('inventory_quantity')
    def _onchange_inventory_quantity(self):
        self.user_id = self.env.user.id

    @api.depends('inventory_quantity_set', 'inventory_diff_quantity', 'product_id')
    def compute_adjustment_value(self):
        for rec in self:
            if rec.inventory_quantity_set:
                rec.adjustment_value = rec.inventory_diff_quantity * rec.product_id.standard_price
            else:
                rec.adjustment_value = 0

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        res = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, package_id=package_id, package_dest_id=package_dest_id)
        adjustment_reason = self.operations_adjustment_reason.id if self.operations_adjustment_reason else False
        res.update(
            {
                'operations_adjustment_reason': adjustment_reason
            }
        )
        return res

    @api.model
    def _get_inventory_fields_write(self):
        fields = super(StockQuant, self)._get_inventory_fields_write()
        fields.extend(['operations_adjustment_reason', 'state', 'adjustment_value', 'user_id'])
        return fields