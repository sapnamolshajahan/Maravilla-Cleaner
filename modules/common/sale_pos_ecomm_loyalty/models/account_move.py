# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import models, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def generate_loyalty_points(self, move):
        move.ensure_one()

        if self.partner_id.has_unpaid_invoices_last_month() and \
                self.env['res.config.settings'].sudo().search([], order='id desc')[0].disallow_overdue:
            _logger.info(_("there are unpaid invoices due in last month, not granting any points"))
            return

        pos_order = self.env['pos.order'].search([
            ('account_move', '=', move.id),
        ], limit=1)
        if not pos_order:
            return self.generate_loyalty_points_sale_order(move)

        return self.generate_loyalty_points_pos(move, pos_order)

    def generate_loyalty_points_pos(self, move, pos_order):
        loyalty_history_obj = self.env['all.loyalty.history']
        today_date = datetime.today().date()
        config = self.env['all.loyalty.setting'].sudo().search([('active', '=', True), ('issue_date', '<=', today_date),
                                                                ('expiry_date', '>=', today_date)])

        if pos_order and config:
            if move.move_type == 'out_invoice' or move.move_type == 'entry':
                partner_id = pos_order.partner_id
                if partner_id.loyalty_active:
                    plus_points = 0.0

                    company_currency = pos_order.company_id.currency_id
                    web_currency = move.currency_id

                    if config.loyalty_basis_on == 'amount':
                        if config.loyality_amount > 0:
                            price = sum([payment.amount for payment in move._get_reconciled_payments()])
                            if company_currency.id != web_currency.id:
                                new_rate = (price * company_currency.rate) / web_currency.rate
                            else:
                                new_rate = price
                            plus_points = int(new_rate / config.loyality_amount)

                    elif config.loyalty_basis_on == 'loyalty_category':
                        for line in pos_order.lines:
                            pos_categ_id = line.product_id.pos_categ_id
                            if pos_categ_id.Minimum_amount > 0:
                                price = sum([payment.amount for payment in move._get_reconciled_payments()])
                                if company_currency.id != web_currency.id:
                                    new_rate = (price * company_currency.rate) / web_currency.rate
                                else:
                                    new_rate = price
                                plus_points += int(new_rate / pos_categ_id.Minimum_amount)

                    if plus_points > 0:
                        is_credit = loyalty_history_obj.search(
                            [('pos_order_id', '=', pos_order.id), ('transaction_type', '=', 'credit')], limit=1)
                        if is_credit:
                            is_credit.write({
                                'points': (plus_points),
                                'state': 'done',
                                'date': datetime.now(),
                                'partner_id': partner_id.id,
                            })

                            move.write({'loyalty_genrate': True, 'genrated_points': (move.genrated_points + plus_points)})
                        else:
                            vals = {
                                'pos_order_id': pos_order.id,
                                'partner_id': pos_order.partner_id.id,
                                'loyalty_config_id': config.id,
                                'date': datetime.now(),
                                'transaction_type': 'credit',
                                'generated_from': 'pos',
                                'points': plus_points,
                                'state': 'done',
                            }
                            loyalty_history_obj.sudo().create(vals)
                            move.write({'loyalty_genrate': True, 'genrated_points': plus_points})
                            self.write({'loyalty_genrate': True, 'genrated_points': plus_points})

    def generate_loyalty_points_sale_order(self, move):
        """
        mainly copied from generate_loyalty_points() in module `sale_pos_ecomm_loyalty`
        """
        sale_order = self.env['sale.order'].search(['|', ('name', '=', move.invoice_origin), ('name', '=', move.ref)],
                                                   limit=1)
        loyalty_history_obj = self.env['all.loyalty.history']
        today_date = datetime.today().date()
        config = self.env['all.loyalty.setting'].sudo().search([('active', '=', True), ('issue_date', '<=', today_date),
                                                                ('expiry_date', '>=', today_date)])

        flag = False
        if sale_order and config:
            if sale_order.website_id:
                if sale_order.website_id.allow_to_loyalty:
                    flag = True
            else:

                flag = True

        if flag:
            if move.move_type == 'out_invoice' or move.move_type == 'entry':
                for rec in sale_order:
                    partner_id = rec.partner_id
                    if partner_id.loyalty_active:
                        plus_points = 0.0

                        company_currency = rec.company_id.currency_id
                        web_currency = rec.pricelist_id.currency_id

                        if config.loyalty_basis_on == 'amount':
                            if config.loyality_amount > 0:
                                price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
                                if company_currency.id != web_currency.id:
                                    new_rate = (price * company_currency.rate) / web_currency.rate
                                else:
                                    new_rate = price
                                plus_points = int(new_rate / config.loyality_amount)

                        if config.loyalty_basis_on == 'loyalty_category':
                            for line in rec.order_line:
                                if not line.discount_line or not line.is_delivery:
                                    if rec.is_from_website:
                                        prod_categs = line.product_id.public_categ_ids
                                        for c in prod_categs:
                                            if c.Minimum_amount > 0:
                                                price = sum(move.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
                                                if company_currency.id != web_currency.id:
                                                    new_rate = (price * company_currency.rate) / web_currency.rate
                                                else:
                                                    new_rate = price
                                                plus_points += int(new_rate / c.Minimum_amount)
                                    else:
                                        prod_categ = line.product_id.categ_id
                                        if prod_categ.Minimum_amount > 0:
                                            price = sum(move.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
                                            if company_currency.id != web_currency.id:
                                                new_rate = (price * company_currency.rate) / web_currency.rate
                                            else:
                                                new_rate = price
                                            plus_points += int(new_rate / prod_categ.Minimum_amount)

                        if plus_points > 0:
                            is_credit = loyalty_history_obj.search(
                                [('order_id', '=', rec.id), ('transaction_type', '=', 'credit')])
                            if is_credit:
                                is_credit.write({
                                    'points': (plus_points),
                                    'state': 'done',
                                    'date': datetime.now(),
                                    'partner_id': partner_id.id,
                                })

                                move.write(
                                    {'loyalty_genrate': True, 'genrated_points': (move.genrated_points + plus_points)})

                            else:
                                vals = {
                                    'order_id': rec.id,
                                    'partner_id': partner_id.id,
                                    'loyalty_config_id': config.id,
                                    'date': datetime.now(),
                                    'transaction_type': 'credit',
                                    'generated_from': 'sale',
                                    'points': plus_points,
                                    'state': 'done',
                                }
                                loyalty_history = loyalty_history_obj.sudo().create(vals)
                                move.write({'loyalty_genrate': True, 'genrated_points': plus_points})
                                self.write({'loyalty_genrate': True, 'genrated_points': plus_points})
                            rec.write({'order_credit_points': plus_points})
