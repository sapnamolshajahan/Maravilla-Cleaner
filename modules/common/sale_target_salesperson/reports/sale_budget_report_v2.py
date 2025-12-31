# -*- coding: utf-8 -*-
from odoo import fields, models, fields, _, tools, api


class SalesBudgetReports(models.Model):
    _name = 'sales.report.budget'
    _description = "Sales Budget Report V2"
    _auto = False
    _rec_name = 'salesperson'
    _order = 'salesperson asc'

    salesperson = fields.Many2one('res.users', string='Salesperson')
    team = fields.Many2one('crm.team', string='Team', related='salesperson.sale_team_id', store=True)
    budget = fields.Float(string='Forecast')
    period_end_date = fields.Date(string='Period Ending')
    actual = fields.Float(string='Actual')
    invoiced = fields.Float(string='Invoiced')
    sale_orders = fields.Float(string='Sale Orders')
    quotes = fields.Float(string='Quotes')
    opportunities = fields.Float(string='Opportunities')


    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW {} AS (
                     WITH aggregated_sales AS (
            SELECT
                so.user_id, so.team_id as team,
                SUM(so.amount_total) AS total_sales,
                sb.date AS period_end_date
            FROM
                sale_order so
            LEFT JOIN sale_sale_budget sb ON sb.partner_id = so.user_id 
            WHERE
                so.state = 'sale'
                AND so.date_order BETWEEN date_trunc('month', sb.date) AND sb.date
            GROUP BY
                so.user_id, so.team_id, sb.date
        ),
        aggregated_invoices AS (
            SELECT
                am.invoice_user_id AS user_id,
                am.team_id AS team,
                SUM(am.amount_total_signed) AS total_invoiced,
                sb.date AS period_end_date
            FROM
                account_move am
            LEFT JOIN sale_sale_budget sb ON sb.partner_id = am.invoice_user_id
            WHERE
                am.move_type = 'out_invoice'
                AND am.invoice_date BETWEEN date_trunc('month', sb.date) AND sb.date
            GROUP BY
                am.invoice_user_id, am.team_id, sb.date
        ),
        aggregated_quotations AS (
            SELECT
                so.user_id, so.team_id AS team,
                SUM(so.amount_total) AS total_quotations,
                sb.date AS period_end_date 
            FROM
                sale_order so
            LEFT JOIN sale_sale_budget sb ON sb.partner_id = so.user_id 
            WHERE
                so.state in ('draft', 'sent')
                AND so.date_order BETWEEN date_trunc('month', sb.date) AND sb.date
            GROUP BY
                so.user_id, so.team_id, sb.date
        ),
        
        aggregated_opportunities AS (
            SELECT
                cl.user_id,
                cl.team_id AS team,
                SUM(cl.expected_revenue) AS total_opportunities,
                sb.date AS period_end_date
            FROM
                crm_lead cl
            LEFT JOIN sale_sale_budget sb ON sb.partner_id = cl.user_id
            LEFT JOIN crm_stage cs ON cs.id = cl.stage_id
            WHERE
                cl.type = 'opportunity'
                AND cs.is_won = TRUE
                AND cl.create_date BETWEEN date_trunc('month', sb.date) AND sb.date
                AND cl.active = TRUE
                AND cl.probability != 0
            GROUP BY
                cl.user_id, cl.team_id, sb.date
        )
        
        SELECT
            row_number() OVER () AS id,
            ru.id AS salesperson,
            crm.id as team,
            COALESCE(MAX(sb.budget), 0) AS budget,
            MAX(sb.date) AS period_end_date,
            SUM(aml.credit - aml.debit) AS actual,
            COALESCE(MAX(ag_invoices.total_invoiced), 0) AS invoiced,
            COALESCE(MAX(ag_sales.total_sales), 0) AS sale_orders,
            COALESCE(MAX(ag_quotations.total_quotations), 0) AS quotes,
            COALESCE(MAX(ag_opportunities.total_opportunities), 0) AS opportunities
        FROM
            res_users ru
            LEFT JOIN crm_team crm ON crm.user_id = ru.id 
            LEFT JOIN sale_sale_budget sb ON sb.partner_id = ru.id 
            LEFT JOIN aggregated_sales ag_sales ON ag_sales.user_id = ru.id AND ag_sales.period_end_date = sb.date
            LEFT JOIN aggregated_invoices ag_invoices ON ag_invoices.user_id = ru.id AND ag_invoices.period_end_date = sb.date
            LEFT JOIN aggregated_quotations ag_quotations ON ag_quotations.user_id = ru.id AND ag_quotations.period_end_date = sb.date
            LEFT JOIN account_move_line aml ON aml.move_id = ag_invoices.user_id
            LEFT JOIN aggregated_opportunities ag_opportunities ON ag_opportunities.user_id = ru.id AND ag_opportunities.period_end_date = sb.date
        WHERE
            ru.share = False
            AND sb.date IS NOT NULL
        GROUP BY
            ru.id, crm.id, sb.date
        ORDER BY
            ru.id, sb.date
    )

         """.format(self._table))
