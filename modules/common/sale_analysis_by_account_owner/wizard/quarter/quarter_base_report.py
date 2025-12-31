# -*- coding: utf-8 -*-
import base64
import calendar as cal
import logging
from io import BytesIO as StringIO

import pandas
import xlsxwriter

from odoo import models, api, _
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

PANDAS_FREQ = {i: 'Q-{}'.format(cal.month_name[i][:3].upper()) for i in range(1, 13)}

QUARTER_KEYS = {
    1: 'quarter_1',
    2: 'quarter_2',
    3: 'quarter_3',
    4: 'quarter_4',
}


class SaleAnalysisReportQuarterlyBase(models.AbstractModel):
    _name = 'quarterly.sale.analysis.report.base'
    _description = 'Quarterly Sale Analysis Report Base'

    @api.model
    def _get_quarter_key(self, month):
        return QUARTER_KEYS[month]

    @api.model
    def get_header(self):
        line = dict()
        line['parent_account_ref'] = 'Parent Account Ref'
        line['parent_account_name'] = 'Parent Account Name'
        line['account_ref'] = 'Account Ref'
        line['account_name'] = 'Account Name'
        line['region'] = 'Region'
        line['rep_name'] = 'Sales Rep'

        line[self._get_quarter_key(1)] = 'Quarter -1'
        line[self._get_quarter_key(2)] = 'Quarter -2'
        line[self._get_quarter_key(3)] = 'Quarter -3'
        line[self._get_quarter_key(4)] = 'Quarter -4'

        line['total_actual'] = 'Total Actual'
        line['budget'] = 'Budget'

        return line

    @api.model
    def get_fieldnames(self):
        return [
            'parent_account_ref',
            'parent_account_name',
            'account_ref',
            'account_name',
            'region',
            'rep_name',
            self._get_quarter_key(1),
            self._get_quarter_key(2),
            self._get_quarter_key(3),
            self._get_quarter_key(4),
            'total_actual',
            'budget'
        ]

    @api.model
    def get_lines(self, wizard):
        pass

    @api.model
    def get_output(self, wizard):
        lines = self.get_lines(wizard)
        fieldnames = self.get_fieldnames()

        data = StringIO()
        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')
        cell_bold = workbook.add_format({'bold': True})

        first_line = "Sales Analysis report for period {start} to {end}".format(start=wizard.period_start,
                                                                                end=wizard.period_to)
        row = 1
        worksheet.write(row, 1, first_line, cell_bold)
        row += 1
        col_headings = self.get_header()
        i = 0
        for k, v in col_headings.items():
            worksheet.write(row, i, v, cell_bold)
            i += 1
        row += 2

        for line in self.get_lines(wizard):
            i = 0
            for k, v in line.items():
                worksheet.write(row, i, v)
                i += 1
            row += 1

        workbook.close()
        data.seek(0)
        job_uuid = self.env.context.get("job_uuid")
        if job_uuid:
            job = self.env["queue.job"].search([('uuid', '=', job_uuid)], limit=1)
            if job:
                self.env["ir.attachment"].create(
                    {
                        "name": 'Sales Analysis Report',
                        "datas": base64.encodebytes(data.read()),
                        "mimetype": "application/octet-stream",
                        "description": "Product Inventory Download",
                        "res_model": job._name,
                        "res_id": job.id,
                    })
        return ("Sale Analysis Report completed - wrote {ct} rows"
                ).format(ct=row)

    @api.model
    def _get_branch_partners(self, partner_ids):
        partner_ids_str = self._get_non_trailing_comma_tuple(partner_ids)
        # Empty partner list is suppose to return ALL partners and ALL branches

        if len(partner_ids) > 0:
            find_all_branch_partners_sql = "select parent_id, id from res_partner where parent_id in %s"
            sql = find_all_branch_partners_sql % partner_ids_str
            self.env.cr.execute(sql)
        else:
            find_all_branch_partners_sql = "select parent_id, id from res_partner where parent_id is not null"
            self.env.cr.execute(find_all_branch_partners_sql)
        ids = [x[0] for x in self.env.cr.fetchall()]
        return ids

    @api.model
    def find_invoices(self, partner_ids, region_ids, sales_rep_ids, wizard):
        search_tuples = [
            ('state', '=', 'posted'),
            ('partner_id.customer_rank', '>', 0),
            ("company_id", "=", self.env.company.id)
        ]

        if wizard.period_start:
            search_tuples.append(('date', '>=', wizard.period_start))

        if wizard.period_to:
            search_tuples.append(('date', '<=', wizard.period_to))

        if partner_ids:
            # Empty partner list is suppose to return ALL partners and ALL branches
            search_tuples.append(('partner_id', 'in', partner_ids))

        if region_ids:
            # Empty region list is suppose to return ALL regions and ALL regions
            search_tuples.append(('partner_id.team_id', 'in', region_ids))

        if sales_rep_ids:
            # Empty sales rep list is suppose to return ALL sales reps and ALL sales reps
            search_tuples.append(("partner_id.user_id", "in", sales_rep_ids))

        invoices = self.env['account.move'].search(search_tuples)

        if not invoices:
            raise UserError(_('No Account Invoices exists with these parameters.'))

        return invoices

    @api.model
    def _get_non_trailing_comma_tuple(self, args):
        tArray = "("
        iteration = 1

        for arg in args:
            if iteration != len(args):
                tArray += str(arg) + ", "
                iteration += 1
            else:
                tArray += str(arg)
                iteration += 1

        tArray += ")"
        return tArray

    @api.model
    def _get_partner_ids(self, wizard):
        partner_ids = wizard.customer.ids
        ids = wizard.customer.ids
        ids.extend(partner_ids)

        # Empty partner list is suppose to return ALL partners and ALL branches
        if len(partner_ids) > 0:
            branch_partner_ids = self._get_branch_partners(partner_ids)
            ids.extend(branch_partner_ids)

        return ids

    @api.model
    def get_fiscal_quarter(self, inv_date):
        """Return quarter key based on the fiscal year (set in the company config)"""
        freq = PANDAS_FREQ.get(int(self.env.company.fiscalyear_last_month))

        try:
            return int(pandas.PeriodIndex([inv_date], freq=freq).strftime('%q')[0])
        except (IndexError, ValueError):
            return 0

    @api.model
    def _get_region_ids(self, wizard):
        return wizard.region.ids

    @api.model
    def _get_sales_rep_ids(self, wizard):
        return wizard.sales_rep.ids

    @api.model
    def _get_sorted_partners(self, partner_ids):
        """ Get a partner record set sorted by partner ref (without parents first). """
        self.env.cr.execute(
            ("select rp.id from res_partner rp  left join res_partner rpp on rp.parent_id = rpp.id "
             "where rp.id in %s order by rpp.ref nulls first, rp.ref"),
            (tuple(partner_ids),)
        )
        partner_ids = [x[0] for x in self.env.cr.fetchall()]
        partners = self.env["res.partner"].browse(partner_ids)
        return partners
