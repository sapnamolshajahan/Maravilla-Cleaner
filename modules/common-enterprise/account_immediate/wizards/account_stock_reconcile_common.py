# -*- coding: utf-8 -*-

from datetime import date
from odoo.exceptions import UserError
from odoo import models, fields, api



class AccountStockReconcileCommon(models.AbstractModel):
    _name = 'account.stock.reconcile.common'


    def build_lines(self, record, default_expense_account):
        if record.difference > 0:
            if record.account_move_line:
                debit_account = record.account_move_line.account_id.id
                credit_account = default_expense_account
            else:
                debit_account = record.product.categ_id.property_stock_valuation_account_id.id
                credit_account = record.product.categ_id.property_account_expense_categ_id.id
        else:
            if record.account_move_line:
                credit_account = record.account_move_line.account_id.id
                debit_account = default_expense_account
            else:
                credit_account = record.product.categ_id.property_stock_valuation_account_id.id
                debit_account = record.product.categ_id.property_account_expense_categ_id.id

        debit_vals = {
            'account_id': debit_account,
            'ref': 'Clear difference from Immediate Accounting',
            'product_id': record.product.id if record.product else False,
            'debit': abs(record.difference),
            'credit': 0.0,
            'date': record.reconciliation_id.date,
            'immediate_reconciled_date': record.reconciliation_id.date
        }

        credit_vals = {
            'account_id': credit_account,
            'ref': 'Clear difference from Immediate Accounting',
            'product_id': record.product.id if record.product else False,
            'credit': abs(record.difference),
            'debit': 0.0,
            'date': record.reconciliation_id.date,
            'immediate_reconciled_date': record.reconciliation_id.date
        }
        vals_list = [(0, 0, debit_vals), (0, 0, credit_vals)]
        return vals_list

    def create_journal_entry(self, record, default_expense_account):
        journal = self.env.company.write_off_journal
        if not journal:
            raise UserError('Set an adjustment journal in settings')
        vals_list = self.build_lines(record, default_expense_account)
        move_id = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': record.reconciliation_id.date,
            'ref': 'Clear difference from Immediate Accounting',
            'line_ids': vals_list
        })
        move_id._post()
        if record.account_move_line:
            record.account_move_line.write({'immediate_reconciled_date': record.reconciliation_id.date})

        return move_id

    def build_write_off_journal(self, difference, inventory_account, default_expense_account, product, as_at_date):
        journal = self.env.company.write_off_journal
        if not journal:
            raise UserError('Set an adjustment journal in settings')
        vals_list = self.build_write_off_lines(difference, inventory_account, default_expense_account,
                                               product, as_at_date)
        move_id = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': as_at_date,
            'ref': 'Clear difference from Immediate Accounting',
            'line_ids': vals_list
        })
        move_id._post(soft=True)


    def build_write_off_lines(self, write_off_amount, inventory_account, default_expense_account,
                              product, as_at_date):
        # if write_off_amount > 0 then credit inventory in GL
        if write_off_amount > 0:
            debit_account = default_expense_account
            credit_account = inventory_account
        else:
            debit_account = inventory_account
            credit_account = default_expense_account
        
        if not isinstance(debit_account, int):
            debit_account = debit_account.id
        if not isinstance(credit_account, int):
            credit_account = credit_account.id

        debit_vals = {
            'account_id': debit_account,
            'ref': 'Clear difference from Immediate Accounting',
            'product_id': product.id,
            'debit': abs(write_off_amount),
            'credit': 0.0,
            'date': as_at_date,
            'immediate_reconciled_date': as_at_date
        }

        credit_vals = {
            'account_id': credit_account,
            'ref': 'Clear difference from Immediate Accounting',
            'product_id': product.id,
            'credit': abs(write_off_amount),
            'debit': 0.0,
            'date': as_at_date,
            'immediate_reconciled_date': as_at_date
        }
        vals_list = [(0, 0, debit_vals), (0, 0, credit_vals)]
        return vals_list

