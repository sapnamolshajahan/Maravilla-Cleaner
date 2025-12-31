from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    operations_adjustment_reason = fields.Many2one('operations.adjustment.reason')

    def _create_account_move(self):
        """ Inherit and add operations_adjustment_reason to account move lines """
        account_move = super()._create_account_move()
        if account_move:
            linked_moves = self.filtered(lambda m: m.account_move_id == account_move)
            for move in linked_moves:
                if move.operations_adjustment_reason:
                    account_move.line_ids.write({
                        'operations_adjustment_reason': move.operations_adjustment_reason.id
                    })

        return account_move

    # def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
    #     res = super(StockMove, self)._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
    #                                cost)
    #     adjstment_reason = self.operations_adjustment_reason.id if self.operations_adjustment_reason else False
    #     res.update({'operations_adjustment_reason': adjstment_reason})
    #     return res
