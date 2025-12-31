from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    immediate_reconciled_date = fields.Date()
    stock_move_id = fields.Many2one('stock.move', string='Stock Move', index='btree_not_null')
