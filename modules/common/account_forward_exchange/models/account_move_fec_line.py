from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMoveFECLine(models.Model):
    _name = 'account.move.fec.line'
    _inherit = 'account.forward.exchange.allocation'
    _description = 'Invoice FEC Line'

    def _compute_invoice_total(self):
        for line in self:
            if line.invoice.move_type == 'in_refund':
                line.invoice_total = line.invoice.amount_untaxed * -1
            else:
                line.invoice_total = line.invoice.amount_untaxed

    invoice = fields.Many2one("account.move", "Invoice", required=True, ondelete='cascade')
    invoice_state = fields.Selection(related="invoice.state", string="State", readonly=True)
    invoice_total = fields.Monetary("Total Untaxed", compute="_compute_invoice_total", readonly=True,
                                    currency_field='fec_currency')

    @api.onchange('fec')
    def onchange_fec(self):
        if self.fec and self.invoice and not self.amount_allocated:
            available = min(self.fec.amount_uncommitted, self.invoice.amount_untaxed)
            self.amount_allocated = available

    @api.onchange('amount_allocated')
    def onchange_amount_allocated(self):
        if self.invoice.move_type == 'in_refund' and self.amount_allocated > 0:
            self.amount_allocated = self.amount_allocated * -1
        if self.amount_allocated > self.fec.amount_uncommitted:
            raise UserError('Amount allocated cannot exceed the amount unallocated on the contract')

    def account_move_fec_line_created_hook(self, new_records):
        return True

    def account_move_fec_line_updated_hook(self, vals):
        return True

    def account_move_fec_line_deleted_hook(self):
        return True

    @api.model_create_multi
    def create(self, vals_list):
        if self.fec.amount_uncommitted < 0:
            raise UserError('Amount allocated cannot exceed the amount unallocated on the contract')

        records = super(AccountMoveFECLine, self).create(vals_list)
        self.account_move_fec_line_created_hook(records)
        return records

    def write(self, vals):
        if self.fec.amount_uncommitted < 0:
            raise UserError('Amount allocated cannot exceed the amount unallocated on the contract')
        self.account_move_fec_line_updated_hook(vals)
        return super(AccountMoveFECLine, self).write(vals)

    def unlink(self):
        self.account_move_fec_line_deleted_hook()
        return super(AccountMoveFECLine, self).unlink()
