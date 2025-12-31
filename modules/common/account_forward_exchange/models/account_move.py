from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_round


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('fec_lines', 'amount_untaxed', 'set_rate')
    def _compute_blended_currency_rate(self):

        self.currency_rate = 1
        for invoice in self.filtered(lambda x: x.fec_lines):
            invoice_total = invoice.amount_untaxed
            if invoice.set_rate:
                currency_rate = invoice.set_rate
            else:
                currency_rate = invoice.currency_id.with_context(date=invoice.date).rate
            total_amount_currency = 0.0
            if invoice_total and invoice.fec_lines:
                fec_total = sum(invoice.fec_lines.mapped(lambda l: abs(l.amount_allocated)))
                floating_total = invoice_total - fec_total
                for fec_line in invoice.fec_lines:
                    total_amount_currency += fec_line.fec.rate * abs(fec_line.amount_allocated)
                total_amount_currency += currency_rate * floating_total

                if total_amount_currency:
                    currency_rate = float_round(total_amount_currency / invoice_total, precision_digits=6)

            invoice.currency_rate = currency_rate

    fec_lines = fields.One2many('account.move.fec.line', 'invoice', 'FEC Allocation', copy=False)
    currency_rate = fields.Float('Blended Currency Rate', compute='_compute_blended_currency_rate', store=True, default=1,
                                 digits=(18, 6))
    fec_mode = fields.Selection(related='company_id.fec_mode', readonly=True)
    set_rate = fields.Float(string='Use Exchange Rate')

    @api.constrains('fec_lines', 'amount_untaxed')
    def validate_fec_allocation(self):
        for invoice in self:
            if len(invoice.fec_lines) != len(invoice.fec_lines.mapped('fec.id')):
                raise ValidationError("A FEC can only be used once on an invoice")
        return True

    def _get_currency_override(self):
        # self.ensure_one()
        for rec in self:
            rate = currency = None
            if rec.fec_mode == 'ibr' and rec.fec_lines:
                currency = rec.currency_id
                rate = rec.currency_rate
            elif rec.fec_mode == 'rbi':
                po = rec.invoice_line_ids.mapped('purchase_line_id.order_id')
                po = po[0] if po else po
                if po.fec_lines:
                    currency = po.currency_id
                    rate = po.currency_rate
            elif rec.set_rate:
                currency = rec.currency_id
                rate = rec.set_rate
            if currency and rate:
                return {'currency_id': currency.id,
                        'rate': rate}
        return None

    def _compute_invoice_taxes_by_group(self):
        info = self._get_currency_override()
        if info:
            return super(AccountMove,self.with_context(account_forward_exchange__force_rate=info))._compute_invoice_taxes_by_group()
        return super(AccountMove, self)._compute_invoice_taxes_by_group()

    @api.onchange('set_rate')
    def compute_using_rate(self):
        for line in self.line_ids:
            line._compute_currency_rate()

    @api.onchange('fec_lines')
    def onchange_fec_lines(self):
        info = self._get_currency_override()
        if info:
            self.line_ids._compute_currency_rate()

    @api.onchange('date')
    def _onchange_invoice_date(self):
        self._inverse_currency_id()

    @api.onchange('currency_id')
    def _inverse_currency_id(self):
        if self.fec_lines:
            fec_currency = self.fec_lines[0].fec.currency
            if fec_currency != self.currency_id:
                raise UserError(
                    'Invoice currency must be the same as FECs currency. Remove FECs before changing the currency.')
        self._compute_blended_currency_rate()
        info = self._get_currency_override()
        if info and 'account_forward_exchange__force_rate' not in self.env.context:
            return super(AccountMove, self.with_context(account_forward_exchange__force_rate=info))._inverse_currency_id()
        return super(AccountMove, self)._inverse_currency_id()

    def action_post(self):
        """
        The currency rate is not read during posting as the code expects the journal entry items are already converted
        to local currency. This is here for just in case some other branch of execution does recalculation.
        Will also check here to make sure FEC is not over-allocated
        Returns: super

        """
        for record in self:
            if record.move_type in ['in_invoice', 'in_refund']:
                if record.fec_lines:
                    fec_total = sum(record.fec_lines.mapped(lambda l: l.amount_allocated))
                    if fec_total and float_compare(abs(fec_total), record.amount_untaxed, precision_digits=2) == 1:
                        raise ValidationError(
                            "Total allocated FEC amounts differ from the invoice amount. Update FEC allocated amount(s) before saving.")
                info = record._get_currency_override()
                if info:
                    record.line_ids._compute_totals()
                    ctx = self.env.context.copy()
                    ctx['account_forward_exchange__force_rate'] = info
                    self.env.context = ctx.copy()
        return super(AccountMove, self).action_post()

    def _check_fec_vs_invoice_total(self):
        """
        Only to be called from api.constrains decorated method
        Returns: None
        """
        for record in self:
            fec_total = sum(record.fec_lines.mapped(lambda l: l.amount_allocated))
        if fec_total and float_compare(fec_total, record.amount_untaxed, precision_digits=2) == 1:
            raise ValidationError(
                "Total allocated FEC amounts exceeds invoice amount. Update FEC allocated amount(s) before saving.")

    @api.constrains('fec_lines')
    def validate_fec_line_over_allocation_fec_line_changed(self):
        self._check_fec_vs_invoice_total()
        return True

    @api.constrains('line_ids')
    def validate_fec_line_over_allocation_invoice_lines_changed(self):
        self._check_fec_vs_invoice_total()
        return True

    def _reverse_moves(self, default_values_list=None, cancel=False):
        credit_moves = super(AccountMove, self)._reverse_moves(default_values_list=default_values_list, cancel=cancel)
        for credit_move in credit_moves:
            origin_move = credit_move.reversed_entry_id
            if origin_move.fec_lines and origin_move.payment_state != 'paid':
                for fec_line in origin_move.fec_lines:
                    fec_line.copy({'invoice': credit_move.id,
                                   'amount_allocated': fec_line.amount_allocated * -1,
                                   'fec': fec_line.fec.id
                                   })
        return credit_moves


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def compute_blended_currency_rate(self, line):
        invoice_total = line.move_id.amount_untaxed
        if line.move_id.set_rate:
            currency_rate = line.move_id.set_rate
        else:
            currency_rate = line.move_id.currency_id.with_context(date=line.move_id.date).rate
        total_amount_currency = 0.0
        if invoice_total and line.move_id.fec_lines:
            fec_total = sum(line.move_id.fec_lines.mapped(lambda l: abs(l.amount_allocated)))
            floating_total = invoice_total - fec_total
            for fec_line in line.move_id.fec_lines:
                total_amount_currency += fec_line.fec.rate * abs(fec_line.amount_allocated)
            total_amount_currency += currency_rate * floating_total

            if total_amount_currency:
                currency_rate = float_round(total_amount_currency / invoice_total, precision_digits=6)

        return currency_rate

    @api.depends('currency_id', 'company_id', 'move_id.date')
    def _compute_currency_rate(self):
        super(AccountMoveLine, self)._compute_currency_rate()
        for line in self:
            if line.move_id.set_rate or line.move_id.fec_lines:
                line.write({'currency_rate':self.compute_blended_currency_rate(line)})
        return

