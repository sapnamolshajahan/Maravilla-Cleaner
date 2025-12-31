# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.tools import SQL

logger = logging.getLogger(__name__)


class AccountStockReconcileDNI(models.TransientModel):
    _inherit = 'account.stock.reconcile.dni'

    pos_order = fields.Many2one('pos.order', string='POS Order')


    def build_dispatched_not_invoiced(self, as_at_date, reconciliation):
        """
       handle any POS transactions that have not been dispatched as at the date
        """

        difference = super(AccountStockReconcileDNI, self).build_dispatched_not_invoiced(as_at_date, reconciliation)
        categories = self.env['product.category'].search([])
        company = self.env.company.id

        query = SQL(
            """
            SELECT sm.id from stock_move sm
            where sm.pos_order_line is not Null 
            and sm.state not in ('done', 'cancel') or (sm.state = 'done' and sm.move_date > %(as_at_date)s) 
            and sm.company_id = %(company)s 
            """,
            as_at_date=as_at_date,
            company=company
        )
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        if results:
            affected_stock_moves = [r[0] for r in results]
            stock_sale_line_set = list(set(affected_stock_moves))
        else:
            stock_sale_line_set = []

        for rec in stock_sale_line_set:
            stock_move = self.env['stock.move'].browse(rec)
            self.create({
                'reconciliation_id': reconciliation.id,
                'pos_order': stock_move.pos_order_line.order_id.id,
                'pickings': [(6, 0, [stock_move.picking_id.id])],
                'product': stock_move.product_id.id,
                'qty_sent': 0.0,
                'value_sent': 0.0,
                'account_moves': False,
                'qty_invoiced': stock_move.product_uom_qty,
                'value_invoiced': stock_move.value,
                'difference': 0 - stock_move.value,
                'account_move_line': False,
                'date': stock_move.move_date,
            })
            difference += 0 - stock_move.value

        return difference

