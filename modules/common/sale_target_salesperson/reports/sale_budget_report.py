# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SaleBudgetReportRun(models.Model):
    _name = 'sale.budget.report.run'
    _description = "Sales Budget Report Run"

    name = fields.Char(string='Run Sequence', default=1)


class SaleBudgetReportSource(models.Model):
    _name = 'sale.budget.report.source'
    _description = "Sales Budget Report Source"

    sale_budget_report_run = fields.Many2one('sale.budget.report.run', string='Run')
    salesperson = fields.Many2one('res.users', string='Salesperson')
    period_start_date = fields.Date(string='Period Starting')
    period_end_date = fields.Date(string='Period Ending')
    budget = fields.Float(string='Budget')
    actual = fields.Float(string='Actual')
    invoiced = fields.Float(string='Invoiced')
    sale_orders = fields.Float(string='Sale Orders')
    quotes = fields.Float(string='Quotes')


class SaleBudgetReport(models.Model):
    _name = 'sale.budget.report'
    _description = "Sales Budget Report"
    _auto = False
    _rec_name = 'salesperson'
    _order = 'period_end_date asc'

    salesperson = fields.Many2one('res.users', string='Salesperson')
    team = fields.Many2one('crm.team', string='Team', related='salesperson.sale_team_id', store=True)
    period_end_date = fields.Date(string='Period Ending')
    budget = fields.Float(string='Budget')
    actual = fields.Float(string='Actual')
    invoiced = fields.Float(string='Invoiced')
    sale_orders = fields.Float(string='Sale Orders')
    quotes = fields.Float(string='Quotes')

    def build_target(self, run_id):
        records = self.env['sale.sale.budget'].search([])
        for rec in records:
            self.env['sale.budget.report.source'].create({
                'sale_budget_report_run': run_id.id,
                'salesperson': rec.user_id.id,
                'period_end_date': rec.date,
                'budget': rec.budget,
                'actual': 0.0,
                'invoiced': 0.0,
                'sale_orders': 0.0,
                'quotes': 0.0
            })
        return

    def build_account_move(self, run_id):
        sql_select = """
            select DATE_TRUNC('month', am.date) as am_month, sum(am.amount_untaxed_signed), res.user_id from account_move am
             left join res_partner res on am.partner_id = res.id 
             where am.move_type in ('out_invoice', 'out_refund') and am.state = 'posted'
             AND res.user_id IS NOT NULL
             group by res.user_id, DATE_TRUNC('month', am.date)

        """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            first_of_month = recs[i][0]

            month_end_date = (first_of_month + relativedelta(months=1, days=-1)).date()

            existing_source = self.env['sale.budget.report.source'].search([
                ('sale_budget_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_end_date', '=', month_end_date)], limit=1)
            if existing_source:
                existing_source.write({'actual': existing_source.actual + amount})
            else:
                self.env['sale.budget.report.source'].create({
                    'sale_budget_report_run': run_id.id,
                    'salesperson': recs[i][2],
                    'period_end_date': month_end_date,
                    'actual': amount
                })

        return

    def build_quotes(self, run_id):
        sql_select = """
            SELECT date_order, amount_untaxed, user_id, invoice_status FROM sale_order
            WHERE state = 'draft' and user_id is not null
        """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            first_of_month = recs[i][0]

            month_end_date = (first_of_month + relativedelta(months=1, days=-1)).date()
            existing_source = self.env['sale.budget.report.source'].search([
                ('sale_budget_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_start_date', '<=', recs[i][0]),
                ('period_end_date', '=', month_end_date)], limit=1)
            if existing_source:
                existing_source.write({'quotes': existing_source.quotes + amount})
            else:
                self.env['sale.budget.report.source'].create({
                    'sale_budget_report_run': run_id.id,
                    'salesperson': recs[i][2],
                    'period_end_date': month_end_date,
                    'quotes': amount
                })

        return

    def build_sale_orders(self, run_id):
        sql_select = """
                select date_order, amount_untaxed, user_id, invoice_status from sale_order 
                where state not in ('draft', 'cancel') AND user_id IS NOT NULL

                    """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            invoice_status = recs[i][3]
            first_of_month = recs[i][0]

            month_end_date = (first_of_month + relativedelta(months=1, days=-1)).date()
            existing_source = self.env['sale.budget.report.source'].search([
                ('sale_budget_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_start_date', '<=', recs[i][0]),
                ('period_end_date', '=', month_end_date)], limit=1)
            if existing_source:
                existing_source.write({'sale_orders': existing_source.quotes + amount})
            else:
                self.env['sale.budget.report.source'].create({
                    'sale_budget_report_run': run_id.id,
                    'salesperson': recs[i][2],
                    'period_end_date': month_end_date,
                    'sale_orders': amount
                })
        return

    def build_account_move_target(self, run_id):
        sql_select = """
            select am.date, am.amount_untaxed_signed, res.user_id from account_move am
             left join res_partner res on am.partner_id = res.id
             where am.move_type in ('out_invoice', 'out_refund') and am.state = 'posted'
             AND res.user_id IS NOT NULL
        """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            first_of_month = recs[i][0]

            month_end_date = (first_of_month + relativedelta(months=1, days=-1))
            existing_source = self.env['sale.budget.report.source'].search([
                ('sale_budget_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_start_date', '<=', recs[i][0]),
                ('period_end_date', '>=', month_end_date)], limit=1)
            if existing_source:
                existing_source.write({'invoiced': existing_source.invoiced + amount})
            else:
                self.env['sale.budget.report.source'].create({
                    'sale_budget_report_run': run_id.id,
                    'salesperson': recs[i][2],
                    'period_end_date': month_end_date,
                    'invoiced': amount
                })
        return

    def build_data_table(self):
        run_id = self.env['sale.budget.report.run'].create({'name': 1})
        self.build_target(run_id)
        self.build_account_move(run_id)
        # self.build_account_move_target(run_id)
        self.build_sale_orders(run_id)
        self.build_quotes(run_id)
        return run_id

    def _select_fields(self):
        select_ = f"""
                    id as id, salesperson, period_end_date, budget, actual, invoiced, sale_orders, quotes
                    """
        return select_

    def _from_model(self):
        return """ sale_budget_report_source"""

    def _where_run(self, run_id):
        return """ sale_budget_report_run = {this_run}""".format(this_run=run_id.id)

    def _query(self):
        run_id = self.build_data_table()
        query = f"""
            SELECT {self._select_fields()}
            FROM {self._from_model()}
            WHERE {self._where_run(run_id)}
        """
        return query

    @property
    def _table_query(self):
        return self._query()
