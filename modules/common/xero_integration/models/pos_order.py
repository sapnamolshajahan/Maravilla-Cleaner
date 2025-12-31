import logging

from odoo import models, fields, api,_
_logger = logging.getLogger(__name__)



class PosOrderXero(models.Model):
    _inherit = 'pos.order'

    ########################################################################################
    # Default & compute methods
    ########################################################################################

    ########################################################################################
    # Fields
    ########################################################################################

    ########################################################################################
    # Functions
    ########################################################################################
    def action_pos_order_invoice(self):
        res = super(PosOrderXero, self).action_pos_order_invoice()
        if res.get('res_id'):
            # Assign default analytic account from operation type linked warehouse - if nothing is set already
            move = self.env['account.move'].browse(res['res_id'])
            self.assign_default_analytic_account(move_lines=move.invoice_line_ids)

        return res

    def write(self, values):
        res = super(PosOrderXero, self).write(values)
        if values.get('state') == 'done':
            for order in self:
                # Assign default analytic account from operation type linked warehouse - if nothing is set already
                order.assign_default_analytic_account(move_lines=self.env['account.move.line'].search([
                    ('move_id', 'in', order.session_id._get_related_account_moves().ids)
                ]))

        return res

    def assign_default_analytic_account(self, move_lines):
        """
        For every move line => assign a default analytic account from warehouse config (if nothing is set already)
        :param move_lines: account.move.line objects
        """
        for line in move_lines:
            if not line.analytic_distribution:  # Check if no distribution is set
                config = self.config_id
                if config and config.picking_type_id:
                    account = config.picking_type_id.warehouse_id.get_default_analytic_account()
                    if account:
                        # Assign 100% to the default analytic account
                        line.analytic_distribution = {str(account): 100}
