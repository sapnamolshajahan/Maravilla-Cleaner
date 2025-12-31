# -*- coding: utf-8 -*-
import logging

from odoo import models, api
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class QuarterlySaleAnalysisReportCategoryGroup(models.TransientModel):
    _name = "quarterly.sale.analysis.report.categorygroup"
    _inherit = 'quarterly.sale.analysis.report.base'
    _description = "Quarterly Sale Analysis Report for Category Group"

    @api.model
    def get_fieldnames(self):
        return ['category_name'] + super(QuarterlySaleAnalysisReportCategoryGroup, self).get_fieldnames()

    @api.model
    def get_header(self):
        header = super(QuarterlySaleAnalysisReportCategoryGroup, self).get_header()
        header['category_name'] = 'Category Name'
        return header

    @api.model
    def get_lines(self, wizard):
        return self._group_by_category(wizard)

    @api.model
    def get_all_data_quarter_category(self, partner_ids, region_ids, sales_rep_ids, wizard):
        sql_select = """
            select pc.name, r2.ref, r2.name, r.ref,r.name,t.name,
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
            """

        where_string = """
            where am.invoice_date >= '{start_date}' and
            am.invoice_date <= '{end_date}' and
            am.company_id = {company} and
            am.move_type in ('out_invoice','out_refund') and
            am.state = 'posted'
            """

        if wizard.category:
            if len(wizard.category) == 1:
                where_string += " and pc.id = {cat_id} "
            else:
                where_string += " and pc.id in {cat_ids} "

        if partner_ids:
            where_string += " and r.id in {partner_ids} "

        if region_ids:
            where_string += " and t.id in {team_ids} "

        if sales_rep_ids:
            where_string += " and u.id in {user_ids} "

        group_by_string = """
            group by pc.name, r2.ref, r2.name, r.ref, r.name, t.name, u_name, am.invoice_date
            order by pc.name, r2.ref, r2.name, r.ref, r.name, t.name, u_name, am.invoice_date
            """

        sql_string = sql_select + where_string + group_by_string
        self.env.cr.execute(sql_string.format(start_date=wizard.period_start,
                                              end_date=wizard.period_to,
                                              company=self.env.company.id,
                                              partner_ids=tuple(partner_ids) if len(partner_ids) > 1 else self.format_tuple(partner_ids),
                                              team_ids=tuple(region_ids) if len(region_ids) > 1 else self.format_tuple(region_ids),
                                              user_ids=tuple(sales_rep_ids) if len(sales_rep_ids) > 1 else self.format_tuple(sales_rep_ids),
                                              cat_ids=tuple(wizard.category.ids) if len(wizard.category.ids) > 1 else self.format_tuple(wizard.category.ids),
                                              cat_id=wizard.category.ids and wizard.category.ids[0]))
        big_list = self.env.cr.fetchall()
        return big_list

    def format_tuple(self,t):
        if len(t) == 1:
            return f'({t[0]})'
        return '(' + ', '.join(map(str, t)) + ')'

    @api.model
    def _group_by_category(self, wizard):
        partner_ids = self._get_partner_ids(wizard)
        region_ids = self._get_region_ids(wizard)
        sales_rep_ids = self._get_sales_rep_ids(wizard)

        # invoices = self.find_invoices(partner_ids, region_ids, sales_rep_ids, wizard)
        # account_invoice_line_dict = self._get_account_invoice_line_by_partner_by_category_dict(wizard, invoices)

        sql_detail = self.get_all_data_quarter_category(partner_ids, region_ids, sales_rep_ids, wizard)

        lines = []
        quarter_keys = [(x, self._get_quarter_key(x)) for x in range(1, 5)]
        line_zeros = dict([(x[1], 0) for x in quarter_keys])
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

            if (category_name == existing_category_name
                    and parent_ref == existing_parent_ref
                    and parent_name == existing_parent_name
                    and account_ref == existing_account_ref
                    and account_name == existing_account_name
                    and region == existing_region
                    and rep_name == existing_rep_name):

                quarter_index = self.get_fiscal_quarter(date)
                quarter_key = self._get_quarter_key(quarter_index)
                line[quarter_key] += amount
                line['total_actual'] += amount
                category_subtotal += amount

            # add a category total line
            elif category_name != existing_category_name:
                lines.append(line)
                line = {
                    "category_name": category_name,
                    "parent_account_ref": "",
                    "parent_account_name": "",
                    "account_ref": "",
                    "account_name": "",
                    "region": "",
                    "rep_name": "",
                    "budget": ""
                }
                for _x, quarter_key in quarter_keys:
                    line[quarter_key] = ''

                line[self._get_quarter_key(4)] = 'Category Subtotal'
                line['total_actual'] = category_subtotal
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
                line = {}
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
                quarter_index = self.get_fiscal_quarter(date)
                quarter_key = self._get_quarter_key(quarter_index)
                line[quarter_key] = amount
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
                quarter_index = self.get_fiscal_quarter(date)
                quarter_key = self._get_quarter_key(quarter_index)
                line[quarter_key] = amount
                line['total_actual'] = amount
                category_subtotal += amount

        return lines

    @api.model
    def _get_quarterly_revenue(self, invoice_lines):
        monthly_revenue_budget_dict = dict()

        for invoice_line in invoice_lines:
            quarter_index = self.get_fiscal_quarter(invoice_line.invoice_id.date_invoice)
            quarter_key = self._get_quarter_key(quarter_index)

            if quarter_key not in monthly_revenue_budget_dict:
                monthly_revenue_budget_dict[quarter_key] = 0

            if invoice_line.invoice_id.move_type == 'out_invoice':
                monthly_revenue_budget_dict[quarter_key] += invoice_line.price_subtotal

            elif invoice_line.invoice_id.move_type == 'out_refund':
                monthly_revenue_budget_dict[quarter_key] -= invoice_line.price_subtotal

        return monthly_revenue_budget_dict

    @api.model
    def _get_account_invoice_line_by_partner_by_category_dict(self, wizard, invoices):
        category_ids = self._get_category_ids(wizard)
        result = dict()

        query = ("select pt.categ_id, am.partner_id, aml.id from account_move_line aml "
                 "join account_move am on aml.move_id = am.id "
                 "join product_product pp on aml.product_id = pp.id "
                 "join product_template pt on pp.product_tmpl_id = pt.id "
                 "where aml.move_id in %s and aml.product_id is not null ")

        params = [tuple(invoices.ids)]

        if category_ids:
            query += "and pt.categ_id in %s"
            params.append(tuple(category_ids))

        self.env.cr.execute(query, tuple(params))

        for category_id, partner_id, line_id in self.env.cr.fetchall():
            result.setdefault(category_id, {}).setdefault(partner_id, []).append(line_id)

        return result

    @api.model
    def _get_category_ids(self, wizard):
        return wizard.category.ids
