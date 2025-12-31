import logging
from datetime import timedelta
from odoo import _, api, fields, models
logger = logging.getLogger(__name__)

def chunk_list(big_list, chunk_size):
    """ Yield successive chunks from a list. """
    for i in range(0, len(big_list), chunk_size):
        yield big_list[i:i + chunk_size]


class StockReconciliationReport(models.TransientModel):
    _name = 'account_immediate.stock.reconciliation.report'
    _description = 'Stock Reconciliation'

    def _end_of_month_date(self):
        date = fields.Date.today()
        return date.replace(day=1) - timedelta(days=1)


    date = fields.Date(string='As At Date', default='_end_of_month_date')

    @api.model
    def get_report_values(self, date=False):
        return {
            'data': self._get_report_data(date=date),
            'context': {},
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = []
        doc = self._get_report_data()
        return {
            'doc_ids': docids,
            'doc_model': 'stock.reconciliation.report',
            'docs': docs,
        }

    def get_inventory_balance(self, date):
        product_model = self.env['product.product']
        products = product_model.with_company(self).search([('is_storable', '=', True)])
        tot_recs = len(products)
        product_value = 0.0
        up_to = 0
        for chunk_ids in chunk_list(products, 250):
            up_to += len(chunk_ids)
            logger.info('Products Processed = {up_to} of {tot_recs}'.format(up_to=up_to, tot_recs=tot_recs))
            for product in chunk_ids:
                product_value += product.with_context(to_date=date).total_value

            product_model._invalidate_cache()

        return product_value

    def get_gl_balance(self, as_at_date):
        categories = self.env['product.category'].search([])
        accounts = list(set([x.property_stock_valuation_account_id.id for x in categories]))
        aml_lines = self.env['account.move.line'].search([
            ('account_id', 'in', accounts),
            ('date', '<=', as_at_date),
            ('parent_state', '=', 'posted')
        ])
        balance = sum([x.debit - x.credit for x in aml_lines])
        return balance

    def get_so_dispatched_not_invoiced(self, date, this_run):
        existing = self.env['account.stock.reconcile.dni'].search([
            ('reconciliation_id', '=', self.id)
        ])
        existing.unlink()
        dni = self.env['account.stock.reconcile.dni'].build_dispatched_not_invoiced(date, this_run)
        return dni

    def get_po_received_not_invoiced(self, date, this_run):
        existing = self.env['account.stock.reconcile.rni'].search([
            ('reconciliation_id', '=', self.id)
        ])
        existing.unlink()
        dni = self.env['account.stock.reconcile.rni'].build_received_not_invoiced(date, this_run)
        return dni

    def get_unexplained(self, date, this_run):
        existing = self.env['account.stock.reconcile.other'].search([
            ('reconciliation_id', '=', self.id)
        ])
        existing.unlink()
        other = self.env['account.stock.reconcile.other'].build_other(date, this_run)
        return other


    def _get_report_data(self, date=False, product_category=False, warehouse=False):
        company = self.env.company
        # Check if date is a string instance
        if isinstance(date, str):
            date = fields.Date.from_string(date)

        if date == fields.Date.today():
            pass
        else:
            pass

        this_run = self.create({
            'date': date
        })
        
        so_dispatched_not_invoiced = self.get_so_dispatched_not_invoiced(date, this_run)
        po_received_not_invoiced = self.get_po_received_not_invoiced(date, this_run)
        inventory_balance = self.get_inventory_balance(date)
        balance_per_gl = self.get_gl_balance(date)
        unexplained = self.get_unexplained(date, this_run)

        report_data = {
            'res_id': this_run.id,
            'date': date,
            'company_id': company.id,
            'currency_id': company.currency_id.id,
            'inventory_balance': "%.2f" % inventory_balance,
            'so_dispatched_not_invoiced': "%.2f" % so_dispatched_not_invoiced,
            'po_received_not_invoiced': "%.2f" % po_received_not_invoiced,
            'unexplained': "%.2f" % unexplained,
            'balance_per_gl': "%.2f" % balance_per_gl,
        }

        return report_data



    @api.model
    def journal_dispatched_not_invoiced(self, date=False):
        return

    @api.model
    def explain_received_not_invoiced(self, date=False):
        return

    @api.model
    def journal_received_not_invoiced(self, date=False):
        return

    @api.model
    def explain_unexplained(self, date=False):
        return

    @api.model
    def journal_unexplained(self, date=False):
        return
