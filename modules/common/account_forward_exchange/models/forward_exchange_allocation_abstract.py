from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountForwardExchangeAllocation(models.AbstractModel):
    _name = 'account.forward.exchange.allocation'
    _description = 'FEC Allocation Abstract'

    fec = fields.Many2one('account.forward.exchange', "FEC", required=True, copy=False, ondelete='restrict',
                          domain="[('state', '!=', 'complete')]")
    committed_costs = fields.Float(related='fec.amount_committed', readonly=True)
    contract_amount = fields.Float(related='fec.amount', string="Contract Amount", readonly=True)
    rate = fields.Float(related='fec.rate', string='Rate', readonly=True, digits=(18, 4))
    amount_allocated = fields.Float("Allocate Amount", required=True, default=0.0)
    fec_currency = fields.Many2one('res.currency', related='fec.currency', readonly=True)

    @api.constrains('amount_allocated')
    def validate_amount_allocated(self):
        for rec in self:
            if not rec.amount_allocated:
                raise ValidationError("FEC 'Allocate Amount' invalid. Must be a non-zero amount")
            if rec.amount_allocated > rec.contract_amount:
                raise ValidationError("FEC 'Allocate Amount' exceeds contract amount")
        return True
