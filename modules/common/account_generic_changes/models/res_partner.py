# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Partner(models.Model):
    """
    Partners can only either be customers or suppliers.
    If there are any associated account.move (journals) the ability to change is disabled.
    """
    _inherit = "res.partner"

    ################################################################################
    # Field Computations
    ################################################################################
    @api.depends("customer_rank")
    def _is_customer(self):
        for r in self:
            r.customer = r.customer_rank > 0

    def _set_customer(self):
        for r in self:
            if r.customer:
                if not r.customer_rank:
                    r.customer_rank = 1
            else:
                if r.customer_rank:
                    r.customer_rank = 0

    @api.depends("supplier_rank")
    def _is_supplier(self):
        for r in self:
            r.supplier = r.supplier_rank > 0

    def _set_supplier(self):
        for r in self:
            if r.supplier:
                if not r.supplier_rank:
                    r.supplier_rank = 1
            else:
                if r.supplier_rank:
                    r.supplier_rank = 0

    def _has_journals(self):
        """
        Determine whether partner has any associated account.moves
        """
        move_model = self.env["account.move"]
        for r in self:
            move = move_model.search([("partner_id", "=", r.id)], limit=1)
            r.has_journals = True if move else False

    def _compute_invoice_overide_values(self):
        """ Force calculate values to empty for performance. """
        if self.env.company.invoiced_set_counts_zero:
            self.total_invoiced = 0
        else:
            self.total_invoiced = self._invoice_total()

    def _compute_journal_items_overide_values(self):
        """ Force calculate values to empty for performance. """
        if self.env.company.journal_set_counts_zero:
            self.journal_item_count = 0
        else:
            self._compute_journal_item_count()

    ################################################################################
    # Fields
    ################################################################################
    customer = fields.Boolean(compute="_is_customer", store=True, inverse="_set_customer", string="Customer")
    supplier = fields.Boolean(compute="_is_supplier", store=True, inverse="_set_supplier", string="Supplier")
    receivables_payables = fields.Char("Receivables & Payables", readonly=True, groups="account.group_account_invoice",
                                       copy=False)
    receivables_payables_unrec = fields.Char("Unreconciled", readonly=True, groups="account.group_account_invoice",
                                             copy=False)
    has_journals = fields.Boolean("Has Journals", compute="_has_journals")
    has_bank_account = fields.Boolean(string='Has bank account', help='Technical field')
    journal_item_count = fields.Integer("Journal Items", readonly=True, compute="_compute_journal_items_overide_values",
                                        store=True)
    total_invoiced = fields.Monetary("Total Invoiced", readonly=True, compute="_compute_invoice_overide_values",
                                     groups="account.group_account_invoice", store=True)
    # here to override the groups set in core odoo as causing funny security issues
    credit_limit = fields.Float(
        string='Credit Limit', help='Credit limit specific to this partner.',
        groups='base.group_user',
        company_dependent=True, copy=False, readonly=False)

    def _compute_journal_item_count(self):
        AccountMoveLine = self.env['account.move.line']
        for partner in self:
            partner.journal_item_count = AccountMoveLine.search_count([('partner_id', '=', partner.id)])
