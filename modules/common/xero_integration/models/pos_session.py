import logging

from odoo import models, fields, api,_
_logger = logging.getLogger(__name__)


class PosSessionRef(models.Model):
    _inherit = 'pos.session'

    ########################################################################################
    # Default & compute methods
    ########################################################################################

    ########################################################################################
    # Fields
    ########################################################################################

    ########################################################################################
    # Functions
    ########################################################################################

    def write(self, values):
        res = super(PosSessionRef, self).write(values)
        if values.get('state') == 'closed':
            for session in self:
                for order in self.env['pos.order'].search([('session_id', '=', session.id)]):
                    # Assign default analytic account from operation type linked warehouse - if nothing is set already
                    order.assign_default_analytic_account(move_lines=self.env['account.move.line'].search([
                        ('move_id', 'in', order.session_id._get_related_account_moves().ids)
                    ]))

        return res
