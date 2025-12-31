# -*- coding: utf-8 -*-
import logging

from odoo import models, api, fields

_log = logging.getLogger(__name__)


class AccountMoveLineExtension(models.Model):
    _inherit = "account.move.line"

    cost_price = fields.Float(string="Cost Price", digits="Accounting")
    blocked = fields.Boolean(
        string='No Follow-up',
        default=False,
        help="You can check this box to mark this journal item as a litigation with the "
             "associated partner",
    )


    @api.onchange('account_id')
    def _onchange_account_id(self):
        for rec in self:
            if rec.account_id and rec.account_id.currency_id:
                rec.currency_id = rec.account_id.currency_id

    def action_display_invoice(self):
        u"""
        This function returns an action that displays the invoice (self).
        """
        self = self.sudo()
        invoice_ids = self.mapped('move_id')
        imd = self.env['ir.model.data']

        if invoice_ids and invoice_ids[0].move_type == 'out_invoice':
            action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
            form_view_id = self.env.ref('account.view_move_form').id
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
            form_view_id = self.env.ref('account.view_move_form').id

        result = {
            'name': action['name'],
            'type': action['type'],
            'help': action['help'],
            'views': [[False, 'list'],
                      [form_view_id, 'form'],
                      [False, 'graph'],
                      [False, 'kanban'],
                      [False, 'calendar'],
                      [False, 'pivot']],
            'target': action['target'],
            'context': action['context'],
            'res_model': action['res_model'],
        }

        if invoice_ids:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]

        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    @api.model
    def _module_install_set_menu_security(self):
        """ Set security on core menu

            We can't do this in XML as some modules delete this menu.
        """
        account_move_menu = self.env.ref("account.menu_action_account_moves_all",
                                         raise_if_not_found=False)
        if account_move_menu:
            account_group = self.env.ref("account.group_account_user",
                                         raise_if_not_found=False)
            if account_group:
                account_move_menu.group_ids = [(4, account_group.id, False)]

    """
    remove standard behaviour that sets the debit or credit value on line create
    at same time populate the label from the previous line 
    """

    @api.model
    def default_get(self, default_fields):
        values = super(AccountMoveLineExtension, self).default_get(default_fields)
        if self._context.get('line_ids') and any(
                field_name in default_fields for field_name in ('debit', 'credit', 'account_id', 'partner_id')):
            move = self.env['account.move'].new({'line_ids': self._context['line_ids']})
            balance = sum(line['debit'] - line['credit'] for line in move.line_ids)
            if balance < 0.0:
                values.update({'debit': 0.0})

            if balance > 0.0:
                values.update({'credit': 0.0})

            line_count = len(self._context['line_ids'])

            if not values.get('name', None) and line_count > 1:
                try:
                    last_row = self._context['line_ids'][line_count - 1][2]

                    if last_row and last_row.get('name'):
                        values['name'] = last_row['name']
                except:
                    pass

        return values

