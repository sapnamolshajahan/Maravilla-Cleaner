# -*- coding: utf-8 -*-
import logging

from odoo import models, api
from odoo.exceptions import UserError

_log = logging.getLogger(__name__)


class MonthlySaleAnalysisReportCategoryGroup(models.TransientModel):
    _name = 'sale.analysis.report.categorygroup'
    _inherit = 'monthly.sale.analysis.report.base'
    _description = 'Sale Analysis Report for Category Group'

    @api.model
    def get_fieldnames(self):
        return ['category_name'] + super(MonthlySaleAnalysisReportCategoryGroup, self).get_fieldnames()

    @api.model
    def get_month_header(self, wizard):
        header = super(MonthlySaleAnalysisReportCategoryGroup, self).get_month_header(wizard)
        header['category_name'] = 'Category Name'
        return header

    @api.model
    def get_lines(self, wizard):
        return self._group_by_category(wizard)

    def get_all_data_month_category(self, partner_ids, region_ids, sales_rep_ids, wizard):

        sql_select = """
            select
            pc.name,
            r2.ref,
            r2.name,
            r.ref,
            r.name,
            t.name,
            (SELECT user_partner.name 
     FROM res_partner user_partner 
     JOIN res_users u2 on u2.partner_id = user_partner.id 
     WHERE u2.id = u.id) as u_name,
            am.invoice_date,
            sum(CASE
                    WHEN am.move_type = 'out_invoice' THEN aml.price_subtotal 
                    ELSE 0 - aml.price_subtotal 
                END) as price_subtotal

            from account_move_line aml

            join account_move am on aml.move_id = am.id
            left join product_product pp on aml.product_id = pp.id
            left join product_template pt on pp.product_tmpl_id = pt.id
            left join product_category pc on pt.categ_id = pc.id
            left join res_partner r on am.partner_id = r.id
            left join res_partner r2 on r.parent_id = r2.id
            left join crm_team t on r.team_id = t.id
            left join res_users u on r.user_id = u.id
            left join res_partner p3 on p3.id = u.partner_id
            """

        where_string = """
            where am.invoice_date >= '{start_date}' and
            am.invoice_date <= '{end_date}' and
            am.company_id = {company} and
            am.move_type in ('out_invoice','out_refund') and 
            am.state = 'posted' """

        if wizard.category:
            if len(wizard.category) == 1:
                where_string += " and pc.id = {0} ".format(wizard.category.ids and wizard.category.ids[0])
            else:
                where_string += " and pc.id in {0} ".format(tuple(wizard.category.ids))

        if partner_ids:
            if len(partner_ids) == 1:
                where_string += " and r.id = {0} ".format(partner_ids[0])
            else:
                where_string += " and r.id in {0} ".format(tuple(partner_ids))

        if region_ids:
            if len(region_ids) == 1:
                where_string += " and t.id = {0} ".format(region_ids[0])
            else:
                where_string += " and t.id in {0} ".format(tuple(region_ids))

        if sales_rep_ids:
            if len(sales_rep_ids) == 1:
                where_string += " and u.id = {0} ".format(sales_rep_ids[0])
            else:
                where_string += " and u.id in {0} ".format(tuple(sales_rep_ids))

        group_by_string = """
        
            group by pc.name, r2.ref, r2.name, r.ref, r.name, t.name, u_name, u.id, am.invoice_date
            order by pc.name, r2.ref, r2.name, r.ref, r.name, t.name, u_name, u.id, am.invoice_date
        """
        sql_string = sql_select + where_string + group_by_string

        self.env.cr.execute(sql_string.format(start_date=wizard.period_start,
                                              end_date=wizard.period_to,
                                              company=self.env.company.id))
        big_list = self.env.cr.fetchall()
        return big_list

    @api.model
    def _group_by_category(self, wizard):
        partner_ids = self._get_partner_ids(wizard)
        region_ids = self._get_region_ids(wizard)
        sales_rep_ids = self._get_sales_rep_ids(wizard)

        sql_detail = self.get_all_data_month_category(partner_ids, region_ids, sales_rep_ids, wizard)

        lines = []
        month_keys = [(x, self.get_month_key(x)) for x in range(1, 13)]
        line_zeros = dict([(x[1], 0) for x in month_keys])
        if not sql_detail:
            raise UserError("No data available for selected arguments")

        existing_category_name = sql_detail[0][0]
        existing_parent_ref = sql_detail[0][1]
        existing_parent_name = sql_detail[0][2]
        existing_account_ref = sql_detail[0][3]
        existing_account_name = sql_detail[0][4]
        existing_region = sql_detail[0][5]
        existing_rep_name = sql_detail[0][6]
        category_subtotal = 0
        line = {
            "category_name": existing_category_name or "",
            "parent_account_ref": existing_parent_ref or "",
            "parent_account_name": existing_parent_name or "",
            "account_ref": existing_account_ref or "",
            "account_name": existing_account_name or "",
            "region": existing_region or "",
            "rep_name": existing_rep_name or "",
            "budget": 0,
            "total_actual": 0
        }
        line.update(line_zeros)

        for sql_line in sql_detail:
            category_name = sql_line[0]
            parent_ref = sql_line[1]
            parent_name = sql_line[2]
            account_ref = sql_line[3]
            account_name = sql_line[4]
            region = sql_line[5]
            rep_name = sql_line[6]
            date = sql_line[7]
            amount = sql_line[8]

            if category_name == existing_category_name and parent_ref == existing_parent_ref \
                    and parent_name == existing_parent_name and account_ref == existing_account_ref \
                    and account_name == existing_account_name and region == existing_region and rep_name == existing_rep_name:
                month_index = self.get_fiscal_month(date)
                month_key = self.get_month_key(month_index)
                line[month_key] += amount
                line['total_actual'] += amount
                category_subtotal += amount

            # add a category total line
            elif category_name != existing_category_name:
                lines.append(line)
                line = {
                    "category_name": existing_category_name,
                    "parent_account_ref": "",
                    "parent_account_name": "",
                    "account_ref": "",
                    "account_name": "",
                    "region": "",
                    "rep_name": "",
                    "budget": ""
                }

                for _x, month_key in month_keys:
                    line[month_key] = ''

                line[self.get_month_key(12)] = 'Category Subtotal'
                line['total_actual'] = category_subtotal
                lines.append(line)

                # Then add another empty line to separate from the next category
                empty_line = line.copy()
                empty_line["category_name"] = ""
                empty_line["total_actual"] = ""
                empty_line[self.get_month_key(12)] = ""
                lines.append(empty_line)

                existing_category_name = sql_line[0]
                existing_parent_ref = sql_line[1]
                existing_parent_name = sql_line[2]
                existing_account_ref = sql_line[3]
                existing_account_name = sql_line[4]
                existing_region = sql_line[5]
                existing_rep_name = sql_line[6]
                date = sql_line[7]
                amount = sql_line[8]

                line = {
                    "category_name": existing_category_name or "",
                    "parent_account_ref": existing_parent_ref or "",
                    "parent_account_name": existing_parent_name or "",
                    "account_ref": existing_account_ref or "",
                    "account_name": existing_account_name or "",
                    "region": existing_region or "",
                    "rep_name": existing_rep_name or "",
                    "budget": 0
                }

                line.update(line_zeros)
                month_index = self.get_fiscal_month(date)
                month_key = self.get_month_key(month_index)
                line[month_key] = amount
                line['total_actual'] = amount
                category_subtotal = amount

            else:
                lines.append(line)
                existing_category_name = sql_line[0]
                existing_parent_ref = sql_line[1]
                existing_parent_name = sql_line[2]
                existing_account_ref = sql_line[3]
                existing_account_name = sql_line[4]
                existing_region = sql_line[5]
                existing_rep_name = sql_line[6]
                date = sql_line[7]
                amount = sql_line[8]

                line = {
                    "category_name": existing_category_name or "",
                    "parent_account_ref": existing_parent_ref or "",
                    "parent_account_name": existing_parent_name or "",
                    "account_ref": existing_account_ref or "",
                    "account_name": existing_account_name or "",
                    "region": existing_region or "",
                    "rep_name": existing_rep_name or "",
                    "budget": 0
                }
                line.update(line_zeros)
                month_index = self.get_fiscal_month(date)
                month_key = self.get_month_key(month_index)
                line[month_key] = amount
                line['total_actual'] = amount
                category_subtotal += amount

        return lines

    @api.model
    def _get_account_invoice_line_by_partner_by_category_dict(self, wizard, invoice_ids):
        category_ids = self._get_category_ids(wizard)
        result = dict()

        query = ("select pt.categ_id, am.partner_id, aml.id from account_move_line aml "
                 "join account_move am on aml.move_id = am.id "
                 "join product_product pp on aml.product_id = pp.id "
                 "join product_template pt on pp.product_tmpl_id = pt.id "
                 "where aml.move_id in %s and aml.product_id is not null ")

        params = [tuple(invoice_ids)]

        if category_ids:
            query += "and pt.categ_id in %s"
            params.append(tuple(category_ids))

        self.env.cr.execute(query, tuple(params))

        for category_id, partner_id, line_id in self.env.cr.fetchall():
            result.setdefault(category_id, {}).setdefault(partner_id, []).append(line_id)

        return result

    @api.model
    def _get_monthly_revenue(self, invoice_lines):
        monthly_revenue_budget_dict = dict()

        for invoice_line in invoice_lines:
            account_invoice = invoice_line.move_id
            month_index = self.get_fiscal_month(account_invoice.invoice_date)
            month_key = self.get_month_key(month_index)

            if month_key not in monthly_revenue_budget_dict:
                monthly_revenue_budget_dict[month_key] = 0

            if account_invoice.type == 'out_invoice':
                monthly_revenue_budget_dict[month_key] += invoice_line.price_subtotal

            elif account_invoice.type == 'out_refund':
                monthly_revenue_budget_dict[month_key] -= invoice_line.price_subtotal

        return monthly_revenue_budget_dict

    def _get_sorted_partners(self, partner_ids):
        """ Get a partner records et sorted by partner ref (without parents first). """
        self.env.cr.execute(
            ("select rp.id from res_partner rp  left join res_partner rpp on rp.parent_id = rpp.id "
             "where rp.id in %s order by rpp.ref nulls first, rp.ref"),
            (tuple(partner_ids),)
        )
        partner_ids = [x[0] for x in self.env.cr.fetchall()]
        partners = self.env["res.partner"].browse(partner_ids)
        return partners

    @api.model
    def _get_category_ids(self, wizard):
        return wizard.category.ids
