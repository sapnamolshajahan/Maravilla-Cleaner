# -*- coding: utf-8 -*-

from datetime import date
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.tools import SQL



class AccountStockReconcileOther(models.TransientModel):
    _name = 'account.stock.reconcile.other'

    reconciliation_id = fields.Many2one('account_immediate.stock.reconciliation.report')
    product = fields.Many2one('product.product', string='Product')
    value_sent = fields.Float(string='Inventory Value')
    account_move = fields.Many2one('account.move', string='Journal')
    value_invoiced = fields.Float(string='GL Value')
    difference = fields.Float(string='Difference')
    source = fields.Char(string='Source')
    product_value = fields.Many2one('product.value', string='Product Value')
    account_move_line = fields.Many2one('account.move.line', string='Account Move Line')
    stock_move = fields.Many2one('stock.move', string='Stock Move')
    reconciled = fields.Boolean(string='Reconciled')
    date = fields.Date(string='Date')

    def get_impact_of_value_change(self, product_value):
        product = product_value.product_id
        query = """
        SELECT
            sm.id AS id,
            sm.product_id,
            sm.date,
            picking.user_id,
            sm.company_id,
            sm.reference,
            CASE WHEN sm.is_in THEN sm.value ELSE -sm.value END AS value,
            CASE WHEN sm.is_in THEN sm.quantity ELSE -sm.quantity END AS quantity,
            'stock.move' AS res_model_name,
            'Operation' AS description
        FROM
            stock_move sm
        LEFT JOIN
            stock_picking picking ON sm.picking_id = picking.id
        LEFT JOIN
            product_product pp ON sm.product_id = pp.id
        LEFT JOIN
            product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN
            product_category pc ON pt.categ_id = pc.id
        LEFT JOIN
            res_company company ON sm.company_id = company.id
        WHERE
            sm.state = 'done' 
            AND sm.product_id = %s 
            AND (sm.is_in = TRUE OR sm.is_out = TRUE)
            -- Ignore moves for standard cost method. Only display the list of cost updates
            AND (
                (pt.categ_id IS NOT NULL AND pc.property_cost_method ->> company.id::text IN ('fifo', 'average'))
                OR (pt.categ_id IS NULL OR pc.property_cost_method IS NULL AND company.cost_method IN ('fifo', 'average'))
            )
        UNION ALL
        SELECT
            -pv.id,
            pv.product_id,
            pv.date,
            pv.user_id,
            pv.company_id,
            'Adjustment' AS reference, -- Set a fixed string for the reference
            pv.value,
            0 AS quantity, -- Set quantity to 0 as requested,
            'product.value' AS res_model_name,
            pv.description
        FROM
            product_value pv
        WHERE
            pv.move_id IS NULL 
            AND pv.product_id = %s
        ;
        """
        self.env.cr.execute(query, [product.id, product.id] )
        result = self.env.cr.fetchall()
        sorted_result = sorted(result, key=lambda x: (x[2], x[3]))
        added_value = 0.0
        total_quantity = total_value = 0.0
        for record in sorted_result:
            if record[8] == 'stock.move':
                added_value = record[6]
                total_value += record[6]
                total_quantity += record[7]
            elif record[8] == 'product.value':
                added_value = (record[6] * total_quantity) - total_value
                total_value = record[6] * total_quantity

            if 0 - record[0] == product_value.id:
                return added_value

        return 0.0

    def create_sm_record(self, sm, reason, reconciliation):
        if sm.location_dest_id.usage == 'internal':
            self.create({
                'reconciliation_id': reconciliation.id,
                'product': sm.product_id.id,
                'value_sent': sm.value,
                'value_invoiced': 0.0,
                'difference': sm.value,
                'source': reason,
                'stock_move': sm.id,
                'date': sm.move_date
            })
        else:
            self.create({
                'reconciliation_id': reconciliation.id,
                'product': sm.product_id.id,
                'value_sent': 0 - sm.value,
                'value_invoiced': 0.0,
                'difference': 0 - sm.value,
                'source': reason,
                'stock_move': sm.id,
                'date': sm.move_date
            })

    def build_not_linked(self, as_at_date):
        not_linked = self.env['stock.move'].search([
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            '|', ('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'internal'),
            ('state', '=', 'done'),
            ('move_date', '<=', as_at_date),
            ('sale_line_id', '=', False),
            ('purchase_line_id', '=', False),
        ])
        return not_linked

    def build_aml_not_handled(self, as_at_date, accounts, qty_updated_am):
        aml_not_handled = self.env['account.move.line'].search([
            ('account_id', 'in', accounts),
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            ('date', '<=', as_at_date),
            ('parent_state', '=', 'posted'),
            ('cogs_origin_id', '=', False),
            ('purchase_line_id', '=', False),
            ('move_id', 'not in', qty_updated_am)
        ])
        return aml_not_handled


    def build_other(self, as_at_date, reconciliation):
        """
        This is the balancing number between perpetual inventory and GL as at the specified date.
        Will potentially include
         - any cost price adjustments in inventory
         - any quantity adjustments in inventory (Note if the location has a GL account then this is done by Odoo)
         - any other stock moves not linked to a sale order or purchase order
         - any GL entries not reconciled by DNI or RNI
         - any GL entries with no product
         NOTE - need to override for POS or MRP
        """
        categories = self.env['product.category'].search([])
        accounts = []
        for category in categories:
            if category.property_stock_valuation_account_id.id not in accounts:
                accounts.append(category.property_stock_valuation_account_id.id)
        accum_difference = 0.0
        qty_updated_am = []

        qty_updated = self.env['stock.move'].search([
            ('is_inventory', '=', True),
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            '|', ('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'internal'),
            ('state', '=', 'done'),
            ('move_date', '<=', as_at_date)
        ])
        for sm in qty_updated:
            if sm.account_move_id:
                qty_updated_am.append(sm.account_move_id.id)
            if sm.location_dest_id.usage == 'internal':
                self.create_sm_record(sm, 'Quantity Updated', reconciliation)
                accum_difference -= sm.value
            else:
                self.create_sm_record(sm, 'Quantity Updated', reconciliation)
                accum_difference += sm.value

        not_linked = self.build_not_linked(as_at_date)

        for sm in not_linked:
            if sm.id in [x.id for x in qty_updated]:
                continue
            if sm.location_dest_id.usage == 'internal':
                self.create_sm_record(sm, 'Not linked to SOL-POL', reconciliation)
                accum_difference -= sm.value
            else:
                self.create_sm_record(sm, 'Not linked to SOL-POL', reconciliation)
                accum_difference += sm.value

        price_updated = self.env['product.value'].search([
            '|', ('immediate_reconciled_date', '=', False), ('immediate_reconciled_date', '>', as_at_date),
            ('accounting_date', '<=', as_at_date)
        ])

        for rec in price_updated:
            # need to work out the value of what has been added, so use the standard Odoo avco audit logic
            # will only be a few each month (hopefully)

            added_value = self.get_impact_of_value_change(rec)
            if added_value:
                self.create({
                    'reconciliation_id': reconciliation.id,
                    'product': rec.product_id.id if rec.product_id else False,
                    'value_sent': added_value,
                    'value_invoiced': 0.0,
                    'difference': 0 - added_value,
                    'source': 'Cost Updated',
                    'product_value': rec.id,
                    'date': rec.accounting_date
                })
                accum_difference -= added_value

        aml_not_handled = self.build_aml_not_handled(as_at_date, accounts, qty_updated_am)

        for aml in aml_not_handled:
            self.create({
                'reconciliation_id': reconciliation.id,
                'product': aml.product_id.id if aml.product_id else False,
                'value_sent': 0.0,
                'value_invoiced': aml.debit - aml.credit,
                'difference': 0 - (aml.debit - aml.credit),
                'source': 'Account Move Line',
                'account_move_line': aml.id,
                'date': aml.date
            })
            accum_difference += aml.debit - aml.credit


        return accum_difference



    def button_reconcile(self):
        categories = self.env['product.category'].search([])
        accounts = list(set([x.property_account_expense_categ_id for x in categories]))
        reconcile_common = self.env['account.stock.reconcile.common']
        default_expense_account = accounts[0]
        for record in self:
            if record.difference:
                reconcile_common.create_journal_entry(record, default_expense_account)
                if record.stock_move:
                    record.stock_move.write({'immediate_reconciled_date': record.reconciliation_id.date})
                elif record.product_value:
                    record.product_value.write({'immediate_reconciled_date': record.reconciliation_id.date})
            record.write({
                'reconciled': True,
                'value_sent': record.value_invoiced if not record.value_sent else record.value_sent,
                'value_invoiced': record.value_sent if not record.value_invoiced else record.value_invoiced,
                'difference': 0.0
            })




