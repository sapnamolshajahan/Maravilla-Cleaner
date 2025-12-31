from odoo import api, fields, models


class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = 'stock.inventory.adjustment.name'

    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    adjusted_amount = fields.Float(string='$ Impact')
    state = fields.Selection([('waiting', 'Waiting Approval'), ('done', 'Done')])

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_quant_ids'):
            quants = self.env['stock.quant'].browse(self.env.context['default_quant_ids']).filtered('inventory_quantity_set')
            res['adjusted_amount'] = sum(
                [quant.inventory_diff_quantity * quant.product_id.standard_price for quant in quants]
            )
            res['state'] = 'done'
            if quants:
                if self.env.company.adjustment_approver:
                    is_approver = True if self.env.company.adjustment_approver.id == self.env.user.id else False
                    if is_approver:
                        res['state'] = 'waiting'
        return res

    def action_apply(self):
        quants = self.quant_ids.filtered('inventory_quantity_set')
        quants.write({'user_id': False, 'state': 'done'})
        res = super(StockInventoryAdjustmentName, self).action_apply()
        return res
