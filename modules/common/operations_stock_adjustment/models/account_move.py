from odoo import api, fields, models, _

class AccountMoveCurrent(models.Model):
    _inherit = 'account.move'

    operations_adjustment_reason = fields.Many2one('operations.adjustment.reason')

    def action_post(self):
        res = super(AccountMoveCurrent, self).action_post()
        for rec in self:
            if rec.stock_move_ids and rec.stock_move_ids.operations_adjustment_reason:
                rec.operations_adjustment_reason = rec.stock_move_ids.operations_adjustment_reason.id
        return res