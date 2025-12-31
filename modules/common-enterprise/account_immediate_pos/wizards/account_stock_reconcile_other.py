# -*- coding: utf-8 -*-

from datetime import date
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.tools import SQL



class AccountStockReconcileOther(models.TransientModel):
    _inherit = 'account.stock.reconcile.other'

    def build_not_linked(self, as_at_date):
        not_linked = self.env['stock.move'].search([
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            '|', ('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'internal'),
            ('state', '=', 'done'),
            ('move_date', '<=', as_at_date),
            ('sale_line_id', '=', False),
            ('purchase_line_id', '=', False),
            ('pos_order_line', '=', False)
        ])
        return not_linked

