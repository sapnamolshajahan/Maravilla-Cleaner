# -*- coding: utf-8 -*-
from odoo import fields, models


class MoveReversalWizard(models.TransientModel):
    """
    Override to include distinct Account and Move dates.
    """
    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        result = super(MoveReversalWizard, self)._prepare_default_reversal(move)
        increment = True
        counter = 2
        if move.move_type == 'out_invoice':
            this_move_type = 'out_refund'
        elif move.move_type == 'out_refund':
            this_move_type = 'out_invoice'
        elif move.move_type == 'in_invoice':
            this_move_type = 'in_refund'
        else:
            this_move_type = 'in_invoice'
        while increment:
            ref = result['ref']
            existing_invoices = self.env['account.move'].search([
                ('partner_id', '=', move.partner_id.id),
                ('ref', '=ilike', ref),
                ('move_type', '=', this_move_type),
                ('id', '!=', move.id)
            ])
            if existing_invoices:
                result['ref'] = result['ref'] + "." + str(counter)
                counter += 1
            else:
                increment = False
        result["invoice_origin"] = move.name
        return result

