from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

# TODO invoicing via the picking confirm does not use the rate of the FECs on the PO. Read below...
""" 
The invoice uses the floating rate of the currency on the invoice. As a result the exchange variance is detected between
invoice lines and stock moves and entries created for the difference when invoice is posted.
Need to cater for this one day when FECs on POs are used. You Lucky winner!
"""


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('fec_lines')
    def _compute_blended_currency_rate(self):
        for po in self:
            po_total = po.amount_untaxed
            floating_rate = po.currency_id.rate
            currency_rate = floating_rate
            total_amount_currency = 0.0
            if po_total and po.fec_lines:
                fec_total = sum(po.fec_lines.mapped('amount_allocated'))
                floating_total = po_total - fec_total
                for fec_line in po.fec_lines:
                    total_amount_currency += fec_line.fec.rate * fec_line.amount_allocated
                total_amount_currency += floating_rate * floating_total

                if total_amount_currency:
                    currency_rate = float_round(total_amount_currency / po_total, precision_digits=4)

            self.currency_rate = currency_rate

    fec_lines = fields.One2many('purchase.order.fec.line', 'purchase_order', 'FEC Allocation')
    currency_rate = fields.Float('Blended Currency Rate', compute='_compute_blended_currency_rate', store=True,
                                 digits=(18, 4))
    fec_mode = fields.Selection(related='company_id.fec_mode', readonly=True)

    @api.constrains('fec_lines', 'amount_untaxed')
    def validate_fec_allocation(self):
        for po in self:
            if not po.fec_lines:
                continue

            if len(po.fec_lines) != len(po.fec_lines.mapped('fec.id')):
                raise ValidationError("A FEC can only be used once on a purchase order")
            fec_total = sum(po.fec_lines.mapped('amount_allocated'))
            if float_compare(fec_total, po.amount_untaxed, precision_digits=2) == 1:
                raise ValidationError(("Total allocated FEC amounts exceeds purchase amount."
                                       "Update FEC allocated amount(s) before saving."))
        return True


    def button_approve(self, force=False):
        if self.fec_lines:
            info = {'currency_id': self.currency_id.id,
                    'rate': self.currency_rate
                    }
            return super(PurchaseOrder, self.with_context(account_forward_exchange__force_rate=info)).button_approve()
        return super(PurchaseOrder, self).button_approve()