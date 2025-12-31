# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.tools import SQL

logger = logging.getLogger(__name__)

def chunk_list(big_list, chunk_size):
    """ Yield successive chunks from a list. """
    for i in range(0, len(big_list), chunk_size):
        yield big_list[i:i + chunk_size]

class AccountStockReconcileDNI(models.TransientModel):
    _name = 'account.stock.reconcile.dni'

    reconciliation_id = fields.Many2one('account_immediate.stock.reconciliation.report')
    sale_order = fields.Many2one('sale.order', string='Sale Order')
    partner = fields.Many2one('res.partner', string='Partner', related='sale_order.partner_id')
    pickings = fields.Many2many('stock.picking', string='Picking')
    product = fields.Many2one('product.product', string='Product')
    qty_sent = fields.Float(string='Qty Dispatched')
    value_sent = fields.Float(string='Value Dispatched')
    account_moves = fields.Many2many('account.move', string='Journal')
    qty_invoiced = fields.Float(string='Qty Invoiced')
    value_invoiced = fields.Float(string='Value Invoiced')
    difference = fields.Float(string='Difference')
    account_move_line = fields.Many2one('account.move.line', string='Account Move Line')
    reconciled = fields.Boolean(string='Reconciled')
    date = fields.Date(string='Date')


    def build_dispatched_not_invoiced(self, as_at_date, reconciliation):
        """
        When a SO is invoiced the entries are for DR COS CR Inventory. This happens
        irrespective if the goods have been shipped or not.
        the aml for the revenue has sale_line_ids to link back to the sale order line.
        the aml has cogs_origin_id to link the COS entry to the revenue line.
        since a single SOL can have multiple invoice lines, we assume here that the sale_line_ids
        are for a single sol.

        we need to identify anything dispatched not invoiced or invoiced not dispatched.
        So we create a combined list of sale order lines and iterate over to build the data
        """
        categories = self.env['product.category'].search([])
        accounts = []
        for category in categories:
            if category.property_stock_valuation_account_id and \
                category.property_stock_valuation_account_id.id not in accounts:
                accounts.append(category.property_stock_valuation_account_id.id)
        expense_accounts = []
        for category in categories:
            if category.property_account_expense_categ_id and \
                category.property_account_expense_categ_id.id not in expense_accounts:
                expense_accounts.append(category.property_account_expense_categ_id.id)
        default_expense_account = expense_accounts[0] if expense_accounts else False
        company = self.env.company.id

        query = SQL(
            """
            SELECT sm.sale_line_id from stock_move sm
            join stock_location sl1 on sm.location_id = sl1.id 
            join stock_location sl2 on sm.location_dest_id = sl2.id 
            where sm.sale_line_id is not Null 
            and ( sm.immediate_reconciled_date is Null or sm.immediate_reconciled_date > %(as_at_date)s) 
            and (sl1.usage = 'customer' or sl2.usage = 'customer') 
            and sm.state = 'done' 
            and sm.move_date <= %(move_as_at_date)s 
            and sm.company_id = %(company)s 
            """,
            as_at_date=as_at_date,
            move_as_at_date=as_at_date,
            company=company
        )
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        if results:
            affected_stock_moves = [r[0] for r in results]
            stock_sale_line_set = list(set(affected_stock_moves))
        else:
            affected_stock_moves = False
            stock_sale_line_set = []

        aml_lines = []
        for account in accounts:
            query = SQL(
                """
                SELECT aml.id from account_move_line aml
                left join account_move_line aml2 on aml.cogs_origin_id = aml2.id
                where aml.account_id = %(account)s  
                and ( aml.immediate_reconciled_date is Null or aml.immediate_reconciled_date > %(as_at_date)s ) 
                and aml.date <= %(as_at_date)s  
                and aml.parent_state = 'posted' 
                and aml.company_id = %(company)s 
                """,
                account=account,
                as_at_date=as_at_date,
                company=company
            )
            self.env.cr.execute(query)
            results = self.env.cr.fetchall()
            if results:
                aml_lines = [r[0] for r in results]


        # build a superset of all possible sale order lines
        aml_model = self.env['account.move.line']
        if aml_lines:
            for chunk_ids in chunk_list(aml_lines, 250):
                lines = aml_model.browse(chunk_ids)
                for line in lines:
                    if line.cogs_origin_id.sale_line_ids:
                        if line.cogs_origin_id.sale_line_ids[0].id not in stock_sale_line_set:
                            stock_sale_line_set.append(line.cogs_origin_id.sale_line_ids[0].id)

                aml_model._invalidate_cache()

        auto_write_off = self.env.company.max_writeoff
        difference = 0.0

        sale_order_line_model = self.env['sale.order.line']
        tot_recs = len(stock_sale_line_set) if stock_sale_line_set else 0
        up_to = 0
        if not stock_sale_line_set:
            return difference
        for chunk_ids in chunk_list(stock_sale_line_set, 250):
            sale_lines = sale_order_line_model.browse(chunk_ids)
            up_to += 250
            logger.info(
                'Sale Lines Processed = {up_to} of {tot_recs}'.format(up_to=up_to, tot_recs=tot_recs))
            for sale_line in sale_lines:
                stock_moves = sale_line.move_ids.filtered(lambda x: x.move_date <= as_at_date and x.state == 'done')
                value_sent = sum([x.value for x in stock_moves])
                invoice_account_move_lines = sale_line.invoice_lines.filtered(lambda x: x.date <= as_at_date 
                and x.parent_state == 'posted')
                cos_invoiced = 0.0
                cos_lines = []
                for invoice_line in invoice_account_move_lines:
                    cos_line = invoice_line.move_id.line_ids.filtered(lambda x: x.cogs_origin_id.id == invoice_line.id \
                                                        and x.account_id.id in accounts)
                    if cos_line:
                        cos_lines.append(cos_line)
                        cos_invoiced += 0 - (cos_line.debit - cos_line.credit)  # credit to inventory, allow for returns
                    # pre19 transactions do not have cogs_origin populated
                    # and the links from stock move have been lost hence the convoluted code below
                    # this is a bit of a hack but once the old stuff is reconciled the code will be ignored
                if not cos_lines:
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
                                    cos_lines.append(aml)
                                    cos_invoiced += 0 - (aml.debit - aml.credit)
                                    break
                
                if cos_lines and abs(value_sent - cos_invoiced) < auto_write_off:
                    if value_sent - cos_invoiced != 0.0:
                        product = sale_line.product_id
                        journal_date = cos_lines[0].date
                        inventory_account = product.categ_id.property_stock_valuation_account_id
                        self.env['account.stock.reconcile.common'].build_write_off_journal(
                            value_sent - cos_invoiced, inventory_account, default_expense_account, product,
                                journal_date)
                    stock_moves.write({'immediate_reconciled_date': as_at_date})
                    for cos_line in cos_lines:
                        cos_line.write({'immediate_reconciled_date': as_at_date})
                    self.env.cr.commit()
                else:
                    self.env['account.stock.reconcile.dni'].create({
                        'reconciliation_id': reconciliation.id,
                        'sale_order': sale_line.order_id.id,
                        'pickings': [(6, 0, [x.picking_id.id for x in stock_moves])],
                        'product': sale_line.product_id.id,
                        'qty_sent': sum([x.product_uom_qty for x in stock_moves]),
                        'value_sent': value_sent,
                        'account_moves': [(6, 0, [x.move_id.id for x in invoice_account_move_lines])],
                        'qty_invoiced': sum([x.quantity for x in invoice_account_move_lines]),
                        'value_invoiced': cos_invoiced,
                        'date': sale_line.order_id.date_order.date(),
                        'difference': value_sent - cos_invoiced,
                        'account_move_line': cos_lines[0].id if cos_lines else False,
                    })
                    difference += value_sent - cos_invoiced
                aml_model._invalidate_cache()

            sale_order_line_model._invalidate_cache()

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
                    picking.move_ids.write({'immediate_reconciled_date': record.reconciliation_id.date})
            if record.account_moves and not record.account_move_line:
                for am in record.account_moves:
                    am.line_ids.write({'immediate_reconciled_date': record.reconciliation_id.date})
            record.write({
                'reconciled': True,
                'value_sent': record.value_invoiced if not record.value_sent else record.value_sent,
                'value_invoiced': record.value_sent if not record.value_invoiced else record.value_invoiced,
                'difference': 0.0
            })

