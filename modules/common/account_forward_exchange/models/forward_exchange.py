# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ForwardExchange(models.Model):
    """
    NOTE NOTE NOTE: When creating invoices/POs programmatically with FEC lines, you might need to trigger the
    onchange_fec_lines onchange before creating! If not, then the blended currency rate will not be used for the
    journal entries
    """
    _name = "account.forward.exchange"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Forward Exchange"

    @api.depends("account_move_fec_lines", "purchase_order_fec_lines")
    def _amount_committed(self):
        queries = [
            """select COALESCE(SUM(amount_allocated),0) FROM account_move_fec_line WHERE fec=%s""",
            """select COALESCE(SUM(amount_allocated),0) FROM purchase_order_fec_line WHERE fec=%s"""
        ]
        for fwdex in self:
            committed = 0
            if fwdex.id:
                for query in queries:
                    self.env.cr.execute(query, (fwdex.id,))
                    committed += self.env.cr.fetchone()[0]
            fwdex.amount_committed = committed
            fwdex.amount_uncommitted = fwdex.amount - committed

    @api.depends("amount_committed")
    def _amount_local(self):

        for r in self:
            effective = r.rate or 1
            r.amount_local = r.amount / effective
            r.amount_committed_local = r.amount_committed / effective
            r.amount_uncommitted_local = r.amount_local - r.amount_committed_local

    @api.depends('amount', 'amount_committed')
    def _get_state(self):
        for record in self:
            if record.amount_committed >= record.amount:
                record.state = 'complete'
            else:
                record.state = 'in-progress'

    ###########################################################################
    # Fields
    ###########################################################################
    name = fields.Char("Name", size=32, readonly=True)
    contract_no = fields.Char("Contract Number", size=256, required=True)
    contract_enter_date = fields.Date("Date Contract Entered Info", required=True)
    currency = fields.Many2one(comodel_name="res.currency", string="Currency Name", required=True)
    due_date = fields.Date("Due Date", required=True)
    rate = fields.Float("Rate", digits=(18, 4), required=True, group_operator=False)
    amount = fields.Float("Amount in foreign currency", digits=(18, 2), required=True)
    amount_committed = fields.Float("Amount committed in foreign currency", compute="_amount_committed", store=True)
    amount_uncommitted = fields.Float("Uncommitted Balance", compute="_amount_committed", store=True)
    amount_local = fields.Float("Amount (Local)", compute="_amount_local", store=True)
    amount_committed_local = fields.Float("Amount Committed (Local)", compute="_amount_local", store=True)
    amount_uncommitted_local = fields.Float("Uncommitted Balance (Local)", compute="_amount_local", store=True)
    state = fields.Selection(selection=[
        ("in-progress", "In Progress"),
        ("complete", "Complete"),
    ], string="State", compute='_get_state', store=True)
    forward_exchange_updates = fields.One2many("account.forward.exchange.update",
                                               inverse_name="fe_contract", string="Forward Exchange Contracts")
    reference = fields.Char("Reference", size=128, required=False)
    account_move_fec_lines = fields.One2many('account.move.fec.line', 'fec', 'Invoice FEC Lines')
    purchase_order_fec_lines = fields.One2many('purchase.order.fec.line', 'fec', 'PO FEC Lines')

    @api.depends('name', 'contract_no')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.name}] {record.contract_no}" if record.name and record.contract_no else record.name or record.contract_no or ""

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign the next FE reference number for each record being created.
        """
        for vals in vals_list:
            nextno = self.env["ir.sequence"].sudo().next_by_code(self._name)
            vals["name"] = nextno
        records = super(ForwardExchange, self).create(vals_list)
        return records

    def overcommitted(self):
        self.ensure_one()
        return self.amount_committed > self.amount

    @api.constrains('currency', 'rate', 'amount')
    def validate_fec_currency_and_rate(self):
        if self.account_move_fec_lines or self.purchase_order_fec_lines:
            raise ValidationError("FEC already committed to Invoice and/or Purchase Orders")
        if self.rate == 0 or self.rate < 0:
            raise ValidationError("Rate must be a positive non-zero number")
        if self.amount == 0 or self.amount < 0:
            raise ValidationError("Contract amount must be a positive non-zero number")
        return True

    @api.constrains('contract_enter_date', 'due_date')
    def validate_fec_dates(self):
        if self.contract_enter_date > self.due_date:
            raise ValidationError("Due Date cannot be earlier than Entered Date")

    def action_in_progress(self):
        self.write({
            "state": "in-progress"
        })
