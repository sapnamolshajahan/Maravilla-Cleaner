# -*- coding: utf-8 -*-
import logging

from odoo import models, api
import xlsxwriter

logger = logging.getLogger(__name__)


class SaleAnalysisReportNoGroup(models.TransientModel):
    _name = 'quarterly.sale.analysis.report.nogroup'
    _inherit = 'quarterly.sale.analysis.report.base'
    _description = 'Quarterly Sale Analysis Report for No Group'

    @api.model
    def get_lines(self, wizard):
        return self._no_grouping(wizard)

    @api.model
    def _no_grouping(self, wizard):
        partner_ids = self._get_partner_ids(wizard)
        region_ids = self._get_region_ids(wizard)
        sales_rep_ids = self._get_sales_rep_ids(wizard)

        lines = []
        invoices = self.find_invoices(partner_ids, region_ids, sales_rep_ids, wizard)
        partner_invoice_dict = {}

        cnt = len(invoices)
        done = 0

        for invoice in invoices:
            done += 1
            logger.info('processed = {up_to} of {count}'.format(up_to=done, count=cnt))

            if invoice.partner_id in partner_invoice_dict:
                partner_invoice_dict[invoice.partner_id].append(invoice)
            else:
                partner_invoice_dict[invoice.partner_id] = [invoice]

        cnt = len(partner_invoice_dict)
        done = 0
        for partner, invoices in sorted(partner_invoice_dict.items(), key=lambda p: p[0].parent_id.id):
            done += 1
            logger.info('processed = {up_to} of {count}'.format(up_to=done, count=cnt))
            revenue_dict = self._get_quarterly_revenue(invoices)

            line = {
                'parent_account_ref': partner.parent_id.ref or "",
                'parent_account_name': partner.parent_id.name or "",
                'account_ref': partner.ref or "",
                'account_name': partner.name,
                'region': partner.team_id.name or "",
                'rep_name': partner.user_id.name or ""
            }

            total_actual = 0

            for i in range(1, 5):
                quarter_key = self._get_quarter_key(i)
                line[quarter_key] = 0.00

                if quarter_key in revenue_dict:
                    monthly_revenue = revenue_dict[quarter_key]

                    if quarter_key in line:
                        line[quarter_key] += monthly_revenue
                    else:
                        line[quarter_key] = monthly_revenue

                    total_actual += monthly_revenue

            line['total_actual'] = total_actual
            line['budget'] = 0
            lines.append(line)

            self.env["account.move.line"].invalidate_recordset()
        return lines

    @api.model
    def _get_quarterly_revenue(self, invoices):
        monthly_revenue_budget_dict = dict()

        for invoice in invoices:
            quarter_index = self.get_fiscal_quarter(invoice.date)
            quarter_key = self._get_quarter_key(quarter_index)

            if quarter_key not in monthly_revenue_budget_dict:
                monthly_revenue_budget_dict[quarter_key] = 0

            if invoice.move_type == 'out_invoice':
                monthly_revenue_budget_dict[quarter_key] += invoice.amount_untaxed

            elif invoice.move_type == 'out_refund':
                monthly_revenue_budget_dict[quarter_key] -= invoice.amount_untaxed

        return monthly_revenue_budget_dict

    @api.model
    def _get_account_invoice_by_partner(self, account_invoice_ids):
        account_invoice_by_partner_dict = dict()
        account_ids_str = self._get_non_trailing_comma_tuple(account_invoice_ids.ids)

        self.env.cr.execute("select partner_id, id from account_move where id in %s" % account_ids_str)
        lines = self.env.cr.fetchall()

        for line in lines:
            if line[0] not in account_invoice_by_partner_dict:
                account_invoice_by_partner_dict[line[0]] = []

            account_invoice_by_partner_dict[line[0]].append(line[1])

        return account_invoice_by_partner_dict
