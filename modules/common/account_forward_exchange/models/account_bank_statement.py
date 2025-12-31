from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_round


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    @api.depends('journal_id')
    def determine_currency(self):
        for record in self:
            if record.journal_id.currency_id and record.journal_id.currency_id.id != self.env.company.currency_id.id:
                record.foreign_currency_account = True
            else:
                record.foreign_currency_account = False

    foreign_currency_account = fields.Boolean(string='Foreign Currency Account',
                                              compute=determine_currency, store=True)


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    fec_contract = fields.Many2one(comodel_name='account.forward.exchange', string='FEC Contract')
    local_amount = fields.Float(string='Local Amount')

    # TODO
    # domain=[('currency', '=', currency_id)]

    @api.onchange('fec_contract')
    def onchange_fec_contract(self):
        if self.fec_contract:
            rate = self.fec_contract.rate
            self.local_amount = float_round(self.amount / rate,
                                            precision_digits=self.env["decimal.precision"].precision_get('Accounting'))
        else:
            self.local_amount = 0.0

    @api.model
    def _prepare_liquidity_move_line_vals(self):
        res = super(AccountBankStatementLine, self)._prepare_liquidity_move_line_vals()
        if self.fec_contract:
            if self.fec_contract:
                res['debit'] = self.local_amount if self.local_amount > 0 else res['debit']
                res['credit'] = abs(self.local_amount) if self.local_amount < 0 else res['credit']
        return res

    @api.model
    def _prepare_counterpart_move_line_vals(self, counterpart_vals, move_line=None):
        res = super(AccountBankStatementLine, self)._prepare_counterpart_move_line_vals(counterpart_vals, move_line=move_line)
        if self.fec_contract:
            res['debit'] = abs(self.local_amount) if self.local_amount < 0 else res['debit']
            res['credit'] = abs(self.local_amount) if self.local_amount > 0 else res['credit']
        return res
