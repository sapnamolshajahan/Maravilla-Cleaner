# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SaleBudgetDashboard(models.Model):
    _name = 'sale.budget.dashboard'
    _description = "Sales Budget Dashboard"
    _rec_name = 'salesperson'
    _order = 'period_end_date asc'

    """
    uses the salesperson on the invoice for actual
    """

    salesperson = fields.Many2one('res.users', string='Salesperson')
    period_end_date = fields.Date(string='Period Ending')
    budget = fields.Float(string='Budget')
    actual = fields.Float(string='Actual')

    def run_cron(self):
        records = self.env['sale.sale.budget'].search([])
        partners = list(set([x.partner_id for x in records if x.partner_id]))
        for partner in partners:
            user_id = self.env['res.users'].search([('id', '=', partner.id)], limit=1)
            if not user_id:
                continue
            budget_lines = records.filtered(lambda x: x.partner_id.id == partner.id and x.date > fields.Date.context_today(self)
                                                        - relativedelta(days=395))

            for line in budget_lines:
                dashboard_rec = self.search([('salesperson', '=', user_id.id), ('period_end_date', '=', line.date)], limit=1)
                if dashboard_rec:
                    dashboard_rec.write({'budget': line.budget})
                else:
                    dashboard_rec = self.create({
                        'salesperson': user_id.id,
                        'period_end_date': line.date,
                        'budget': line.budget
                    })
                first_of_next_month = line.date + relativedelta(days=1)
                from_date = first_of_next_month + relativedelta(months=-1)
                sql_select = """
                            select sum(am.amount_untaxed_signed) from account_move am
                             where am.move_type in ('out_invoice', 'out_refund') and am.state = 'posted' 
                             and am.invoice_user_id = {user_id} and am.date >= '{from_date}' and am.date <= '{to_date}'
                        """.format(user_id=user_id.id, from_date=from_date, to_date=line.date)
                self.env.cr.execute(sql_select)
                recs = self.env.cr.fetchall()
                try:
                    amount = recs[0][0]
                    if isinstance(amount, float):
                        dashboard_rec.write({'actual': amount})
                except:
                    pass
