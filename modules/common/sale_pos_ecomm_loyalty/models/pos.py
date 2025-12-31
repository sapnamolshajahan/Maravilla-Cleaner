# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo import fields, models, api, _, tools

_logger = logging.getLogger(__name__)


class pos_category(models.Model):
    _inherit = 'pos.category'

    Minimum_amount = fields.Integer("Amount For loyalty Points")
    amount_footer = fields.Integer('Amount', related='Minimum_amount')

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['Minimum_amount']
        return params


class pos_order(models.Model):
    _inherit = 'pos.order'

    final_loyalty = fields.Float()
    redeem_point = fields.Float()
    redeem_done = fields.Boolean(default=False)

    @api.model
    def sync_from_ui(self, orders):
        result = super().sync_from_ui(orders)
        order_ids = [order['id'] for order in result['pos.order']]
        loyalty_history_obj = self.env['all.loyalty.history']
        today_date = datetime.datetime.today().date()
        loyalty_setting = self.env['all.loyalty.setting'].search(
            [('active', '=', True), ('issue_date', '<=', today_date),
             ('expiry_date', '>=', today_date)])
        if loyalty_setting:
            for order_id in order_ids:
                pos_order_id = self.browse(order_id)
                customer = pos_order_id.partner_id

                if pos_order_id.state not in ['paid', 'done', 'invoiced']:
                    continue

                for order in result['pos.order']:
                    order_loyalty = order.get('final_loyalty')

                    account_move = pos_order_id.account_move

                    if order_loyalty > 0 and not account_move.amount_residual and customer.loyalty_active:
                        exists = loyalty_history_obj.search([
                            ('pos_order_id', '=', pos_order_id.id),
                            ('transaction_type', '=', 'credit')
                        ], limit=1)
                        if not exists:
                            vals = {
                                'pos_order_id': pos_order_id.id,
                                'partner_id': pos_order_id.partner_id.id,
                                'loyalty_config_id': loyalty_setting.id,
                                'date': datetime.datetime.now(),
                                'transaction_type': 'credit',
                                'generated_from': 'pos',
                                'points': order_loyalty,
                                'state': 'done',
                            }
                            loyalty_history_obj.create(vals)

                    if order.get('redeem_done') == True:
                        vals = {
                            'pos_order_id': pos_order_id.id,
                            'partner_id': pos_order_id.partner_id.id,
                            'loyalty_config_id': loyalty_setting.id,
                            'date': datetime.datetime.now(),
                            'transaction_type': 'debit',
                            'generated_from': 'pos',
                            'points': order.get('redeem_point'),
                            'state': 'done',
                        }
                        loyalty_history_obj.create(vals)

        return result


class POSSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        data += ['all.loyalty.setting', 'all.redeem.rule']
        return data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
