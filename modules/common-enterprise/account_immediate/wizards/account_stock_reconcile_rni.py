# -*- coding: utf-8 -*-

from datetime import date
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.tools import SQL



class AccountStockReconcileRNI(models.TransientModel):
    _name = 'account.stock.reconcile.rni'



    reconciliation_id = fields.Many2one('account_immediate.stock.reconciliation.report')
    purchase_order = fields.Many2one('purchase.order', string='Purchase Order')
    partner = fields.Many2one('res.partner', string='Partner', related='purchase_order.partner_id')
    pickings = fields.Many2many('stock.picking', string='Picking')
    product = fields.Many2one('product.product', string='Product')
    qty_sent = fields.Float(string='Qty Received')
    value_sent = fields.Float(string='Value Received')
    account_moves = fields.Many2many('account.move', string='Journal')
    qty_invoiced = fields.Float(string='Qty Invoiced')
    value_invoiced = fields.Float(string='Value Invoiced')
    difference = fields.Float(string='Difference')
    account_move_line = fields.Many2one('account.move.line', string='Account Move Line')
    reconciled = fields.Boolean(string='Reconciled')
    date = fields.Date(string='Date')


    def build_received_not_invoiced(self, as_at_date, reconciliation):
        """
        When a PO is invoiced the entries are for DR Inventory CR Accounts Payable. This happens
        irrespective if the goods have been received or not.
        the aml for the inventory has purchase_line_id.

        we need to identify anything received not invoiced or invoiced not reeived.
        So we create a combined list of purchase order lines and iterate over to build the data
        """
        categories = self.env['product.category'].search([])
        accounts = []
        for category in categories:
            if category.property_stock_valuation_account_id.id not in accounts:
                accounts.append(category.property_stock_valuation_account_id.id)
        expense_accounts = []
        for category in categories:
            if category.property_account_expense_categ_id.id not in expense_accounts:
                expense_accounts.append(category.property_account_expense_categ_id.id)
        default_expense_account = expense_accounts[0] if expense_accounts else False
        company = self.env.company.id
        aml_model = self.env['account.move.line']
        affected_stock_moves = self.env['stock.move'].search([
            ('purchase_line_id', '!=', False),
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            '|', ('location_id.usage', '=', 'supplier'), ('location_dest_id.usage', '=', 'supplier'),
            ('state', '=', 'done'),
            ('move_date', '<=', as_at_date),
            ('company_id', '=', company)
        ])
        aml_lines = self.env['account.move.line'].search([
            ('account_id', 'in', accounts),
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            ('date', '<=', as_at_date),
            ('parent_state', '=', 'posted'),
            ('purchase_line_id', '!=', False)
        ])

        # build a superset of all possible purchase order lines

        stock_purchase_line_set = list(set([x.purchase_line_id for x in affected_stock_moves]))
        auto_write_off = self.env.company.max_writeoff

        for aml in aml_lines:
            if aml.purchase_line_id not in stock_purchase_line_set:
                stock_purchase_line_set.append(aml.purchase_line_id)

        difference = 0.0
        for purchase_line in stock_purchase_line_set:
            stock_moves = affected_stock_moves.filtered(lambda x: x.purchase_line_id.id == purchase_line.id)
            value_received = sum([x.value for x in stock_moves])
            account_move_lines = aml_lines.filtered(lambda x: x.purchase_line_id.id == purchase_line.id)
            if account_move_lines and len(account_move_lines) == 1:
                account_move_line = account_move_lines[0].id
            else:
                account_move_line = False
            inventory_account = False
            value_invoiced = abs(sum([x.debit - x.credit for x in account_move_lines])) # to allow for returns
            
            # deal with legacy lines as no direct link in inventory account
            if not account_move_line:
                for stock_move in stock_moves:
                    picking_name = stock_move.picking_id.name
                    if picking_name:
                        possible_aml = []
                        try:    #TODO getting an error - need to fix
                            possible_aml = aml_model.search([
                            ('account_id', 'in', accounts),
                            ('product_id', '=', stock_move.product_id.id),
                            ('date', '=', stock_move.move_date),
                            ('immediate_reconciled_date', '=', False),
                            ])
                        except:
                            pass
                        for aml in possible_aml:
                            
                            if picking_name in aml.name:
                                account_move_line = aml.id
                                value_invoiced += aml.debit - aml.credit
                                break
            
            if abs(value_received - value_invoiced) < auto_write_off:
                if value_received - value_invoiced != 0.0:
                    product = purchase_line.product_id
                    inventory_account = product.categ_id.property_stock_valuation_account_id
                    self.env['account.stock.reconcile.common'].build_write_off_journal(
                        value_invoiced - value_received, inventory_account, default_expense_account, product,
                        as_at_date)
                stock_moves.write({'immediate_reconciled_date': as_at_date})
                account_move_lines.write({'immediate_reconciled_date': as_at_date})
            else:
                self.create({
                    'reconciliation_id': reconciliation.id,
                    'purchase_order': purchase_line.order_id.id,
                    'pickings': [(6, 0, [x.picking_id.id for x in stock_moves])],
                    'product': purchase_line.product_id.id,
                    'qty_sent': sum([x.product_uom_qty for x in stock_moves]),
                    'value_sent': value_received,
                    'account_moves': [(6, 0, [x.move_id.id for x in account_move_lines])],
                    'qty_invoiced': sum([x.quantity for x in account_move_lines]),
                    'value_invoiced': value_invoiced,
                    'difference': value_received - value_invoiced,
                    'account_move_line': account_move_line,
                    'date': purchase_line.order_id.date_order.date(),
                })
                difference -= value_received - value_invoiced

        return difference


    def button_reconcile(self):
        categories = self.env['product.category'].search([])
        accounts = list(set([x.property_account_expense_categ_id for x in categories]))
        default_expense_account = accounts[0]
        reconcile_common = self.env['account.stock.reconcile.common']
        for record in self:
            if record.difference:
                reconcile_common.create_journal_entry(record, default_expense_account)
                for picking in record.pickings:
                    picking.move_ids.write({'immediate_reconciled_date': self.reconciliation_id.date})
            if record.account_moves and not record.account_move_line:
                for am in record.account_moves:
                    am.line_ids.write({'immediate_reconciled_date': self.reconciliation_id.date})
            record.write({
                'reconciled': True,
                'value_sent': record.value_invoiced if not record.value_sent else record.value_sent,
                'value_invoiced': record.value_sent if not record.value_invoiced else record.value_invoiced,
                'difference': 0.0
            })



