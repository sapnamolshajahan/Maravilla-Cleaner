# -*- coding:utf-8 -*-
from odoo import models, fields,api
from odoo.tools import SQL, Query



class ResPartner(models.Model):
    _inherit = "res.partner"

    #####################################################################################
    # Default and compute methods
    #####################################################################################
    def _get_total_receivable(self):

        for rec in self:
            if rec.credit_limit:
                remaining_credit = rec.calculate_remaining_credit()
                rec.total_receivable = rec.credit if rec.customer_rank > 0 else rec.debit
                rec.credit_remaining = remaining_credit
            else:
                rec.total_receivable = rec.credit_remaining = 0

    #####################################################################################
    # Fields
    #####################################################################################
    warning_type = fields.Selection([
        ("none", "None"),
        ("blocked", "Blocked"),
        ("value", "Value"),
        ("all", "All"),
    ], string="Warning Type", required=True, copy=False, default="all")

    credit_limit = fields.Float(string="Credit Limit", copy=False)
    total_receivable = fields.Float(string="Total Receivable", compute="_get_total_receivable")

    credit_remaining = fields.Float(
        string="Credit Remaining",
        compute="_get_total_receivable",
        help="Credit Limit - Total Receivable - Uninvoiced Confirmed Sale Orders - Unconfirmed Invoices")

    over_credit = fields.Boolean(string="Allow Over Credit?")

    #####################################################################################
    # Model methods
    #####################################################################################
    def calculate_remaining_credit(self):

        self.ensure_one()
        sql_select = """
            select sum(price_subtotal) from sale_order so
            join sale_order_line sol on sol.order_id = so.id
            where so.partner_id = {partner} 
            and so.invoice_status = 'to invoice'
            and sol.invoice_status = 'to invoice'
        """
        self.env.cr.execute(sql_select.format(partner=self.id))
        uninvoiced = 0.0
        for r in self.env.cr.fetchall():
            if r[0]:
                uninvoiced = r[0]
            break

        sql_select = """
            select sum(amount_total) from account_move
            where partner_id = {partner} 
            and state = 'draft'
        """
        self.env.cr.execute(sql_select.format(partner=self.id))
        draft_invoices_amount = 0.0
        for r in self.env.cr.fetchall():
            if r[0]:
                draft_invoices_amount = r[0]
            break
        return self.credit_limit - self.credit - uninvoiced - draft_invoices_amount


    @api.depends_context('company')
    def _credit_debit_get(self):
        query = self.env['account.move.line']._search([
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.env.company.id)
        ])

        tables = query.from_clause.code
        where_clause = query.where_clause.code
        where_params = []
        for clause in query._where_clauses:
            where_params.extend(clause.params)
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = " AND " + where_clause
        self._cr.execute("""SELECT account_move_line.partner_id, a.account_type, SUM(account_move_line.amount_residual)
                          FROM """ + tables + """
                          LEFT JOIN account_account a ON (account_move_line.account_id = a.id)
                          LEFT JOIN account_move am ON (account_move_line.move_id = am.id)
                          WHERE a.account_type IN ('asset_receivable', 'liability_payable')
                          AND account_move_line.partner_id IN %s
                          AND am.payment_state != 'paid'
                          """ + where_clause + """
                          GROUP BY account_move_line.partner_id, a.account_type
                          """, where_params)
        treated = self.browse()
        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if type == 'asset_receivable':
                partner.credit = val
                if partner not in treated:
                    partner.debit = False
                    treated |= partner
            elif type == 'liability_payable':
                partner.debit = -val
                if partner not in treated:
                    partner.credit = False
                    treated |= partner
        remaining = (self - treated)
        remaining.debit = False
        remaining.credit = False
