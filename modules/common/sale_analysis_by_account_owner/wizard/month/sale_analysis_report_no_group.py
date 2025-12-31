# -*- coding: utf-8 -*-
import logging
import string

from odoo import models, api
import xlsxwriter

logger = logging.getLogger(__name__)

VALID_FILE_NAME_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
MONTH_KEYS = {
    1: 'mnth_1',
    2: 'mnth_2',
    3: 'mnth_3',
    4: 'mnth_4',
    5: 'mnth_5',
    6: 'mnth_6',
    7: 'mnth_7',
    8: 'mnth_8',
    9: 'mnth_9',
    10: 'mnth_10',
    11: 'mnth_11',
    12: 'mnth_12',
}


class SaleAnalysisReportNoGroup(models.TransientModel):
    _name = 'sale.analysis.report.nogroup'
    _inherit = 'monthly.sale.analysis.report.base'
    _description = 'Sale Analysis Report for No Group'

    @api.model
    def get_lines(self, wizard):
        return self._no_grouping(wizard)

    @api.model
    def _no_grouping(self, wizard):
        partner_ids = self._get_partner_ids(wizard)
        region_ids = self._get_region_ids(wizard)
        sales_rep_ids = self._get_sales_rep_ids(wizard)
        lines = []

        logger.info("Started fetching invoices for Sale Analysis Report")
        all_invoices = self.find_invoices(partner_ids, region_ids, sales_rep_ids, wizard)
        logger.info("Finished fetching invoices for Sale Analysis Report")

        partner_invoice_dict = {}
        partner_ids_used = set()

        cnt = len(all_invoices)
        done = 0
        for invoices in self.chunk_list(all_invoices, 1000):
            for invoice_data in invoices:
                done += 1
                logger.info('processed invoice_data = {up_to} of {count}'.format(up_to=done, count=cnt))

                # Parse sql data
                partner_id = invoice_data[1]

                invoice_dict = {
                    'invoice_id': invoice_data[0],
                    'partner_id': invoice_data[1],
                    'partner_ref': invoice_data[2],
                    'partner_name': invoice_data[3],
                    'parent_ref': invoice_data[4],
                    'parent_name': invoice_data[5],
                    'team': invoice_data[6],
                    'user': invoice_data[7],
                    'invoice_type': invoice_data[8],
                    'amount_untaxed': invoice_data[9],
                    'date_invoice': invoice_data[10],
                }

                if partner_id in partner_ids_used:
                    partner_invoice_dict[partner_id].append(invoice_dict)
                else:
                    partner_invoice_dict[partner_id] = [invoice_dict]
                    partner_ids_used.add(partner_id)
            
        cnt = len(partner_ids_used)
        done = 0

        for partner_id, invoice_dicts in partner_invoice_dict.items():
            done += 1

            logger.info('processed partners = {up_to} of {count}'.format(up_to=done, count=cnt))
            monthly_revenue_dict = self._get_monthly_revenue(invoices=invoice_dicts)
            invoice = invoice_dicts[0]

            line = dict()

            line['parent_account_ref'] = invoice['parent_ref']
            line['parent_account_name'] = invoice['parent_name']
            line['account_ref'] = invoice['partner_ref']
            line['account_name'] = invoice['partner_name']
            line['region'] = ""
            line['rep_name'] = ""
            line['region'] = invoice['team'] or ""
            line['rep_name'] = invoice['user'] or ""
            total_actual = 0

            for i in range(1, 13):
                month_key = self.get_month_key(i)
                line[month_key] = 0

                if month_key in monthly_revenue_dict:
                    monthly_revenue = monthly_revenue_dict[month_key]
                    line[month_key] = monthly_revenue
                    total_actual += monthly_revenue

            line['total_actual'] = total_actual
            line['budget'] = self.get_budget_for_partner(invoice['partner_id'], wizard.period_start)
            lines.append(line)

        return lines

    @api.model
    def get_budget_for_partner(self, partner_id, date_from):
        """
        This method calculates the budget for a partner.
        Step 1: Sale budget spread for the fiscal years that are involved.
        Step 2: Get the budget allocation for the customer.
        Step 3: Calculate the budget per period by multiplying budget with period spread.
        """
        # removed in migration from V11 to V16 as WSP not using customer budgets

        return False

    @api.model
    def _get_account_invoice_by_partner(self, account_invoice_ids):
        account_invoice_by_partner_dict = dict()
        account_ids_str = self._get_non_trailing_comma_tuple(account_invoice_ids)

        self.env.cr.execute("select partner_id, id from account_move where id in %s" % account_ids_str)
        lines = self.env.cr.fetchall()

        for line in lines:
            if line[0] not in account_invoice_by_partner_dict:
                account_invoice_by_partner_dict[line[0]] = []

            account_invoice_by_partner_dict[line[0]].append(line[1])
        return account_invoice_by_partner_dict

    @api.model
    def _get_monthly_revenue(self, invoices):
        monthly_revenue_budget_dict = dict()

        for invoice in invoices:
            month_index = self.get_fiscal_month(invoice['date_invoice'])
            month_key = self.get_month_key(month_index)

            if month_key not in monthly_revenue_budget_dict:
                monthly_revenue_budget_dict[month_key] = 0

            if invoice['invoice_type'] == 'out_invoice':
                monthly_revenue_budget_dict[month_key] += invoice["amount_untaxed"]

            elif invoice['invoice_type'] == 'out_refund':
                monthly_revenue_budget_dict[month_key] -= invoice["amount_untaxed"]

        return monthly_revenue_budget_dict
