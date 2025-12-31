# -*- coding: utf-8 -*-
import base64
import logging
import string
from io import BytesIO as StringIO

import xlsxwriter

from odoo import models, fields, api

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

MONTH_NAMES = ['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', '']


class SaleAnalysisReportMonthlyBase(models.AbstractModel):
    _name = 'monthly.sale.analysis.report.base'
    _description = 'Monthly Sale Analysis Report Base'

    @api.model
    def get_month_key(self, month):
        return MONTH_KEYS[month]

    @api.model
    def get_month_name(self, month):
        return MONTH_NAMES[month]

    @api.model
    def get_month_header(self, wizard):
        # convert column headings to meaningful values MMM-YY
        line = {}
        line['parent_account_ref'] = 'Parent Account Ref'
        line['parent_account_name'] = 'Parent Account Name'
        line['account_ref'] = 'Account Ref'
        line['account_name'] = 'Account Name'
        line['region'] = 'Region'
        line['rep_name'] = 'Sales Rep'

        report_end_date = fields.Date.from_string(wizard.period_to)
        end_month = report_end_date.month
        fiscal_year_last_month = int(self.env.company.fiscalyear_last_month)

        if report_end_date:
            year = report_end_date.year
        else:
            year = fields.Date.from_string(fields.Date.context_today(self)).year

        year_adj = False
        for i in range(1, 13):

            this_month = fiscal_year_last_month + i
            if this_month > 12:
                this_month = fiscal_year_last_month + i - 12

            mth_string = MONTH_NAMES[this_month]

            if fiscal_year_last_month + i > 12 and not year_adj and not this_month <= fiscal_year_last_month:
                year -= 1
                year_adj = True

            if this_month > end_month:
                line[self.get_month_key(i)] = mth_string + '-' + str(year - 1)
            else:
                line[self.get_month_key(i)] = mth_string + '-' + str(year)

        line['total_actual'] = 'Total Actual'
        line['budget'] = 'Budget'
        return line

    @api.model
    def get_lines(self, wizard):
        return []

    @api.model
    def get_fieldnames(self):
        return [
            'parent_account_ref',
            'parent_account_name',
            'account_ref', 'account_name',
            'region',
            'rep_name',
            self.get_month_key(1),
            self.get_month_key(2),
            self.get_month_key(3),
            self.get_month_key(4),
            self.get_month_key(5),
            self.get_month_key(6),
            self.get_month_key(7),
            self.get_month_key(8),
            self.get_month_key(9),
            self.get_month_key(10),
            self.get_month_key(11),
            self.get_month_key(12),
            'total_actual',
            'budget'
        ]

    @api.model
    def chunk_list(self, big_list, chunk_size=500):
        for i in range(0, len(big_list), chunk_size):
            yield big_list[i:i + chunk_size]

    @api.model
    def get_output(self, wizard):
        data = StringIO()
        workbook = xlsxwriter.Workbook(data, {'in_memory': True})
        worksheet = workbook.add_worksheet('Data')
        cell_bold = workbook.add_format({'bold': True})

        first_line = "Sales Analysis report for period {start} to {end}".format(start=wizard.period_start,
                                                                                end=wizard.period_to)
        row = 1
        worksheet.write(row, 0, first_line, cell_bold)
        row += 1
        col_headings = self.get_month_header(wizard)
        i = 0
        for k, v in col_headings.items():
            worksheet.write(row, i, v, cell_bold)
            i += 1
        row += 2

        for lines in self.chunk_list(self.get_lines(wizard)):
            for line in lines:
                i = 0
                for k, v in line.items():
                    if isinstance(v, dict):
                        v = list(v.values())[0]
                    worksheet.write(row, i, v)
                    i += 1
                row += 1
        pass
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
    def find_invoices(self, partner_ids, region_ids, sales_rep_ids, wizard):
        sql_select = """
            SELECT
            am.id,
            r.id,
            r.ref,
            r.name,
            r2.ref,
            r2.name,
            t.name,
            (SELECT user_partner.name 
     FROM res_partner user_partner 
     JOIN res_users u2 on u2.partner_id = user_partner.id 
     WHERE u2.id = u.id) as u_name,
            am.move_type,
            am.amount_untaxed,
            am.invoice_date 
            FROM account_move_line aml
            JOIN account_move am on aml.move_id = am.id
            LEFT JOIN product_product pp on aml.product_id = pp.id
            LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
            LEFT JOIN product_category pc on pt.categ_id = pc.id
            LEFT JOIN res_partner r on aml.partner_id = r.id
            LEFT JOIN res_partner r2 on r.parent_id = r2.id
            LEFT JOIN crm_team t on r.team_id = t.id
            LEFT JOIN res_users u on r.user_id = u.id
            LEFT JOIN res_users u2 on r2.user_id = u2.id
            LEFT JOIN res_partner p3 on p3.id = u.partner_id
            """

        where_string = """
            WHERE am.invoice_date >= '{start_date}' AND
            am.invoice_date <= '{end_date}' AND
            am.company_id = {company} AND
            am.move_type IN ('out_invoice','out_refund') AND
            am.state = 'posted' """

        if wizard.category:
            if len(wizard.category) == 1:
                where_string += " AND pc.id = {0} ".format(wizard.category.ids and wizard.category.ids[0])
            else:
                where_string += " AND pc.id IN {0} ".format(tuple(wizard.category.ids))

        if partner_ids:
            if len(partner_ids) == 1:
                where_string += " AND r.id = {0} ".format(partner_ids[0])
            else:
                where_string += " AND r.id IN {0} ".format(tuple(partner_ids))

        if region_ids:
            if len(region_ids) == 1:
                where_string += " AND t.id = {0} ".format(region_ids[0])
            else:
                where_string += " AND t.id IN {0} ".format(tuple(region_ids))

        if sales_rep_ids:
            if len(sales_rep_ids) == 1:
                where_string += " AND (u.id = {0} OR u2.id = {1}) ".format(sales_rep_ids[0], sales_rep_ids[0])
            else:
                where_string += " AND (u.id IN {0} OR u2.id IN {1}) ".format(tuple(sales_rep_ids), tuple(sales_rep_ids))

        group_by_string = """
            GROUP BY r2.ref, r2.name, r.ref, r.name, t.name, u_name, u.id, am.invoice_date,  am.id, r.id
            ORDER BY r2.ref, r2.name, r.ref, r.name, t.name, u_name, u.id, am.invoice_date,  am.id, r.id
        """
        sql_string = sql_select + where_string + group_by_string

        self.env.cr.execute(sql_string.format(start_date=wizard.period_start,
                                              end_date=wizard.period_to,
                                              company=self.env.company.id))
        return self.env.cr.fetchall()

    @api.model
    def _get_branch_partners(self, partner_ids):
        if len(partner_ids) > 0:
            return self.env["res.partner"].search([("parent_id", "in", partner_ids)])

        return self.env["res.partner"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("parent_id", "!=", False)
            ])

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
        ids = []
        ids.extend(partner_ids)

        # Empty partner list is suppose to return ALL partners and ALL branches
        if len(partner_ids) > 0:
            branch_partners = self._get_branch_partners(partner_ids)
            ids.extend(branch_partners.ids)

        return ids

    @api.model
    def _get_region_ids(self, wizard):
        return wizard.region.ids

    @api.model
    def _get_sales_rep_ids(self, wizard):
        return wizard.sales_rep.ids

    @api.model
    def get_fiscal_month(self, inv_date):
        """Return month key based on the fiscal year (set in the company config)"""
        month_invoice = fields.Date.from_string(inv_date).month
        fiscal_year_last_month = int(self.env.company.fiscalyear_last_month)

        month_idx = {i: i for i in range(1, 13)}

        if fiscal_year_last_month != 12:
            month_idx = {}

            for i in range(1, 13):
                actual_index = i + (12 - fiscal_year_last_month)

                if actual_index > 12:
                    actual_index -= 12

                month_idx[i] = actual_index

        return month_idx.get(month_invoice)
