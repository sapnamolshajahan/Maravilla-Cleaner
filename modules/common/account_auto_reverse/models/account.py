# -*- coding: utf-8 -*-

from datetime import date
from odoo.exceptions import UserError
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    auto_reverse = fields.Boolean(string='Create Reversal', copy=False)
    reverse_move_id = fields.Many2one(comodel_name='account.move', string='Reversing Journal', copy=False)
    reversal_of_move_id = fields.Many2one(comodel_name='account.move', string='Reversal of Journal', copy=False)
    reversal_accounting_date = fields.Date(string='Accounting Date for Reversal', copy=False)

    @api.onchange('date')
    def onchange_accounting_date(self):
        if self.auto_reverse:
            self.onchange_auto_reverse()

    @api.onchange('auto_reverse')
    def onchange_auto_reverse(self):
        if self.auto_reverse:
            journal_date = self.date
            year = journal_date.year
            month = journal_date.month + 1

            if month == 13:
                year += 1
                month = 1

            day = 1
            self.reversal_accounting_date = date(year, month, day)

    def _auto_reverse_move(self, date=None, journal_id=None, source_move=None):
        self.ensure_one()
        if source_move:
            ref = 'Reversal of: ' + source_move.name
        else:
            ref = 'Reversal of: ' + self.ref
        reversed_move = self.copy(default={
            'date': date,
            'journal_id': journal_id.id if journal_id else self.journal_id.id,
            'ref': ref,
            'reversal_of_move_id': self.id,
            'reverse_move_id': False,
            'auto_reverse': False
        })
        reversed_move.write({
            'ref': ref,
        })
        for acm_line in reversed_move.line_ids.with_context(check_move_validity=False):
            acm_line.write({
                'debit': acm_line.credit,
                'credit': acm_line.debit,
                'amount_currency': -acm_line.amount_currency
            })
        return reversed_move

    def auto_reverse_moves(self, am, date=None, journal_id=None):
        date = date or fields.Date.today()
        reversed_moves = self.env['account.move']

        for ac_move in self:
            reversed_move = ac_move._auto_reverse_move(date=date,
                                                       journal_id=journal_id, source_move=am)
            reversed_moves |= reversed_move

        if reversed_moves:
            reversed_moves.action_post()
            return [x.id for x in reversed_moves]
        return []

    def action_post(self):
        if not self:
            return super(AccountMove, self).action_post()

        for move in self:
            if move.move_type != 'entry':
                return super(AccountMove, self).action_post()

        result = super(AccountMove, self).action_post()
        self.check_auto_reverse()
        return result

    def check_auto_reverse(self):

        for am in self:
            if not am.auto_reverse:
                continue

            if am.reverse_move_id and am.reverse_move_id.state == 'posted':
                raise UserError("You already have a reversing move that is posted. Uncheck the auto-reverse checkbox \
                                 and remember to manually fix the reversing entry after you post these changes")

            if am.reverse_move_id and am.reverse_move_id.state != 'posted':
                am.reverse_move_id.unlink()

            else:
                if not self.reversal_accounting_date:
                    new_date = self.get_reversal_date()
                else:
                    new_date = self.reversal_accounting_date

                reverse_move_id = self.auto_reverse_moves(am, new_date, am.journal_id)
                am.write({'reverse_move_id': reverse_move_id[0]})

    def get_reversal_date(self):
        journal_date = self.date
        year = journal_date.year
        month = journal_date.month + 1

        if month == 13:
            year += 1
            month = 1

        day = 1
        return date(year, month, day)
