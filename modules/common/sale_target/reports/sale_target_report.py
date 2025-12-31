# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class SaleTargetReportRun(models.Model):
    _name = 'sale.target.report.run'
    _description = "Sales target Report Run"

    name = fields.Char(string='Run Sequence', default=1)


class SaleTargetReportSource(models.Model):
    _name = 'sale.target.report.source'
    _description = "Sales target Report Source"

    sale_target_report_run = fields.Many2one('sale.target.report.run', string='Run')
    sale_target_year = fields.Many2one('sale.target.year', string='Year')
    team_id = fields.Many2one(comodel_name='crm.team', string="Sales Team")
    salesperson = fields.Many2one('res.users', string='Salesperson')
    period_start_date = fields.Date(string='Period Starting')
    period_end_date = fields.Date(string='Period Ending')
    target = fields.Float(string='Target')
    actual = fields.Float(string='Actual')
    invoiced = fields.Float(string='Invoiced')
    sale_orders = fields.Float(string='Sale Orders')
    quotes = fields.Float(string='Quotes')


class SaleTargetReport(models.Model):
    _name = 'sale.target.report'
    _description = "Sales target Report"
    _auto = False
    _rec_name = 'sale_target_year'
    _order = 'period_end_date asc'


    sale_target_year = fields.Many2one('sale.target.year', string='Year')
    team_id = fields.Many2one(comodel_name='crm.team', string="Sales Team")
    salesperson = fields.Many2one('res.users', string='Salesperson')
    period_end_date = fields.Date(string='Period Ending')
    target = fields.Float(string='Target')
    actual = fields.Float(string='Actual')
    invoiced = fields.Float(string='Invoiced')
    sale_orders = fields.Float(string='Sale Orders')
    quotes = fields.Float(string='Quotes')

    def check_year_in_full(self, targets):
        start_date = end_date = False
        for target in targets.sorted(lambda x: x.from_date, reverse=False):
            if not start_date and not end_date:
                start_date = target.from_date
                end_date = target.to_date
                continue
            if (target.from_date - end_date).days != 1:
                raise UserError ('Dates not congruent - see {end_date} and {from_date}'.format(end_date=end_date, from_date=target.from_date ))
            end_date = target.to_date

        year_check = end_date + relativedelta(years=-1, days=1)
        if start_date - year_check:
            raise UserError('Dates do not cover full year - see {end_date} and {start_date}'.format(end_date=end_date, start_date=start_date))

    def build_target(self, run_id):
        years = self.env['sale.target.year'].search([])
        for year in years:
            targets = self.env['sale.target'].search([('sale_target_year', '=', year.id)])
            for target in targets:
                splits = self.env['sale.target.split'].search([('sale_target_year', '=', year.id)])
                if splits:
                    self.check_year_in_full(splits)
                    for split in splits:
                        self.env['sale.target.report.source'].create({
                            'sale_target_report_run': run_id.id,
                            'sale_target_year': year.id,
                            'team_id': target.salesperson.sale_team_id.id,
                            'salesperson': target.salesperson.id,
                            'period_start_date': split.from_date,
                            'period_end_date': split.to_date,
                            'target': round(target.target * split.weighting / 100, 2),
                            'actual': 0.0,
                            'invoiced': 0.0,
                            'sale_orders': 0.0,
                            'quotes': 100
                        })

        return

    def build_account_move(self, run_id):
        include_invoiced = self.env.company.include_invoiced
        sql_select = """
            select am.date, am.amount_untaxed_signed, res.user_id from account_move am
             left join res_partner res on am.partner_id = res.id 
             where am.move_type in ('out_invoice', 'out_refund') and am.state = 'posted' 
        """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            existing_source = self.env['sale.target.report.source'].search([
                ('sale_target_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_start_date', '<=', recs[i][0]),
                 ('period_end_date','>=', recs[i][0])
            ], limit=1)
            if existing_source and include_invoiced:
                existing_source.write({'actual': existing_source.actual + amount, 'invoiced': existing_source.invoiced + amount})
            elif existing_source:
                existing_source.write({'invoiced': existing_source.invoiced + amount})
        return

    def build_sale_orders(self, run_id):
        include_sale_orders = self.env.company.include_confirmed_orders
        sql_select = """
                select date_order, amount_untaxed, user_id, invoice_status from sale_order 
                where state not in ('draft', 'cancel')
                    """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            invoice_status = recs[i][3]
            existing_source = self.env['sale.target.report.source'].search([
                ('sale_target_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_start_date', '<=', recs[i][0]),
                ('period_end_date', '>=', recs[i][0])
            ], limit=1)
            if existing_source and include_sale_orders:
                if invoice_status == 'invoiced':
                    existing_source.write({'sale_orders': 1000})
                else:
                    existing_source.write({'actual': existing_source.actual + amount,
                                           'sale_orders': 200})
            elif existing_source:
                existing_source.write({'sale_orders': 300})

        return

    def build_quotes(self, run_id):
        include_quote_orders = self.env.company.include_quote_orders
        sql_select = """
                        select date_order, amount_untaxed, user_id, invoice_status from sale_order 
                        where state = 'draft'
                            """
        self.env.cr.execute(sql_select)
        recs = self.env.cr.fetchall()
        for i in range(0, len(recs)):
            amount = recs[i][1]
            existing_source = self.env['sale.target.report.source'].search([
                ('sale_target_report_run', '=', run_id.id),
                ('salesperson', '=', recs[i][2]),
                ('period_start_date', '<=', recs[i][0]),
                ('period_end_date', '>=', recs[i][0])
            ], limit=1)
            if existing_source and include_quote_orders:
                existing_source.write({'actual': existing_source.actual + amount,
                                       'quotes': existing_source.quotes + amount})
            elif existing_source:
                existing_source.write({'quotes': existing_source.quotes + amount})
        return

    def build_data_table(self):
        run_id = self.env['sale.target.report.run'].create({'name': 1})
        self.build_target(run_id)
        return run_id

    def _select_fields(self):
        select_ = f"""
                    id as id, sale_target_year, team_id, salesperson, period_end_date, target, actual, invoiced, sale_orders, quotes 
                    """
        return select_

    def _from_model(self):
        return """ sale_target_report_source"""

    def _where_run(self, run_id):
        return """ sale_target_report_run = {this_run}""".format(this_run=run_id.id)

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
