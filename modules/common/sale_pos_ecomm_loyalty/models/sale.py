# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from datetime import date, time, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,SQL
from odoo.exceptions import UserError, ValidationError
import logging
from collections import defaultdict
import math

_logger = logging.getLogger(__name__)

class web_category(models.Model):
	_inherit = 'product.category'

	Minimum_amount  = fields.Integer("Amount For loyalty Points")
	amount_footer = fields.Integer('Amount', related='Minimum_amount')

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	order_credit_points = fields.Integer(string='Order Credit Points',copy=False)
	order_redeem_points = fields.Integer(string='Order Redeemed Points',copy=False)
	redeem_value = fields.Float(string='Redeem point value',copy=False)
	is_from_website = fields.Boolean("Is from Website",copy=False,readonly=True)

	loyalty_point_credit=fields.Float(string="Your Loyalty Balance:",readonly=True,copy=False)

	def action_confirm(self):
		res = super(SaleOrder,self).action_confirm()

		for order in self:
			if order.website_id:
				task = self.with_delay(
					channel=self.light_job_channel(),
					description="Post Web Order Notification"
				).post_notification_for_web_orders(
					so_id=order.id,
					uid=self.env.user.id,
				)

				"""
				Create invoice automatically for webstore orders.
				Do not create orders if automatic invoice is configured; this will be called in the automatic invoice
				function, causing duplicated sale order creation and errors no line errors.
				"""
				if not self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice'):
					invoice = order._create_invoices()
					if invoice.company_id.auto_confirm_customer_invoice:
						invoice.action_post()
				self.with_delay(
					channel=self.light_job_channel(),
					description="Send Invoice For Web Orders"
				).send_invoice_for_web_orders(
					so_id=order.id,
				)

		loyalty_history_obj = self.env['all.loyalty.history']
		today_date = datetime.today().date()
		config = self.env['all.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
								('expiry_date', '>=', today_date )])
		if config :
			for rec in self:
				partner_id =rec.partner_id
				if partner_id.loyalty_active:
					if rec.order_redeem_points > 0:
						is_debit = loyalty_history_obj.search([('order_id','=',rec.id),('transaction_type','=','debit')])
						if is_debit:
							is_debit.write({
								'points': rec.order_redeem_points,
								'state': 'done',
								'date' : datetime.now(),
								'partner_id': partner_id.id,
							})
						else:
							vals = {
								'order_id':rec.id,
								'partner_id': partner_id.id,
								'loyalty_config_id' : config.id,
								'date' : datetime.now(),
								'transaction_type' : 'debit',
								'generated_from' : 'sale',
								'points': rec.order_redeem_points,
								'state': 'done',
							}
							loyalty_history = loyalty_history_obj.sudo().create(vals)
		return res
	
	def action_cancel(self):		
		res = super(SaleOrder,self).action_cancel()
		loyalty_history_obj = self.env['all.loyalty.history']	
		for rec in self:
			loyalty = loyalty_history_obj.search([('order_id','=',rec.id)])
			for l in loyalty:
				l.write({
					'state' : 'cancel'
				})
		return res


	def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
		res = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
		if res.get('quantity') != 0 :
			self.ensure_one()
			OrderLine = self.env['sale.order.line']
			line = OrderLine.sudo().browse(line_id)
			if line and line.discount_line :
				line.write({
					'price_unit' : - line.redeem_points * line.order_id.redeem_value
				})
		return res
		

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	discount_line = fields.Boolean(string='Discount line',readonly=True,copy=False)
	redeem_points = fields.Integer(string='Redeem Points',copy=False)
	redeem_value = fields.Float(string='Redeem point value',copy=False)



class AccountMoveInherit(models.Model):
	_inherit = 'account.move'

	loyalty_genrate = fields.Boolean("loyalty genrated")
	genrated_points = fields.Integer("Loyalty Genrated")

	def button_draft(self):		
		res = super(AccountMoveInherit,self).button_draft()
		loyalty_history_obj = self.env['all.loyalty.history']
		sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)],limit=1)
		if sale_order:
			for rec in sale_order:
				loyalty = loyalty_history_obj.search([('order_id','=',rec.id)])
				for l in loyalty:
					l.write({
						'state' : 'cancel'
					})
		return res

	def _reverse_moves(self, default_values_list=None, cancel=False):
		''' Reverse a recordset of account.move.
		If cancel parameter is true, the reconcilable or liquidity lines
		of each original move will be reconciled with its reverse's.

		:param default_values_list: A list of default values to consider per move.
									('type' & 'reversed_entry_id' are computed in the method).
		:return:                    An account.move recordset, reverse of the current self.
		'''
		if not default_values_list:
			default_values_list = [{} for move in self]

		if cancel:
			lines = self.mapped('line_ids')
			# Avoid maximum recursion depth.
			if lines:
				lines.remove_move_reconcile()

		reverse_type_map = {
			'entry': 'entry',
			'out_invoice': 'out_refund',
			'out_refund': 'entry',
			'in_invoice': 'in_refund',
			'in_refund': 'entry',
			'out_receipt': 'entry',
			'in_receipt': 'entry',
		}

		move_vals_list = []
		for move, default_values in zip(self, default_values_list):
			default_values.update({
				'move_type': reverse_type_map[move.move_type],
				'reversed_entry_id': move.id,
			})
			move_vals_list.append(move.with_context(move_reverse_cancel=cancel)._reverse_move_vals(default_values, cancel=cancel))

		reverse_moves = self.env['account.move'].create(move_vals_list)

		if reverse_moves.genrated_points > reverse_moves.partner_id.loyalty_pts:
			today_date = datetime.today().date()
			config = self.env['all.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
									('expiry_date', '>=', today_date )])
			inv_lines = []
			if config :
				redeem_prod_id = config.product_id
				inv_lines.append({
						'product_id': config.product_id.id,
						'name': config.product_id.name,
						'price_unit': -(reverse_moves.genrated_points * config.loyality_amount),
						'move_id': reverse_moves.id,
					})

				reverse_moves.write({
					'invoice_line_ids': [(0, 0, l) for l in inv_lines],
				})
		for move, reverse_move in zip(self, reverse_moves.with_context(check_move_validity=False, move_reverse_cancel=cancel)):
			if move.date != reverse_move.date:
				for line in reverse_move.line_ids:
					if line.currency_id:
						line._onchange_currency()
			reverse_move._recompute_dynamic_lines(recompute_all_taxes=False)

		reverse_moves._check_balanced(reverse_moves)

		if cancel:
			reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
			for move, reverse_move in zip(self, reverse_moves):
				group = defaultdict(list)
				for line in (move.line_ids + reverse_move.line_ids).filtered(lambda l: not l.reconciled):
					group[(line.account_id, line.currency_id)].append(line.id)

				
				for (account, dummy), line_ids in group.items():
					if account.reconcile or account.internal_type == 'liquidity':
						self.env['account.move.line'].browse(line_ids).with_context(move_reverse_cancel=cancel).reconcile()

		return reverse_moves
	
	def generate_loyalty_points(self,move):
		if move.move_type == 'out_invoice':
			sale_order = self.env['sale.order'].search([('name','=',move.invoice_origin)],limit=1)	
			if sale_order:
				loyalty_history_obj = self.env['all.loyalty.history']   
				today_date = datetime.today().date()
				config = self.env['all.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
										('expiry_date', '>=', today_date )])
				for con in config:
					if con : 
						for rec in sale_order:
							partner_id =rec.partner_id
							plus_points = 0.0

							company_currency = rec.company_id.currency_id
							web_currency = rec.pricelist_id.currency_id
							if partner_id.loyalty_active:
								if con.loyalty_basis_on == 'amount' :
									if con.loyality_amount > 0 :
										price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
										if company_currency.id != web_currency.id:
											new_rate = (price*company_currency.rate)/web_currency.rate
										else:
											new_rate = price
										plus_points =  int( new_rate / con.loyality_amount)

								if con.loyalty_basis_on == 'loyalty_category' :
									for line in  rec.order_line:
										if not line.discount_line or not line.is_delivery :
											if rec.is_from_website :
												prod_categs = line.product_id.public_categ_ids
												for c in prod_categs :
													if c.Minimum_amount > 0 :
														price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
														if company_currency.id != web_currency.id:
															new_rate = (price*company_currency.rate)/web_currency.rate
														else:
															new_rate = price
														plus_points += int(new_rate / c.Minimum_amount)
											else:
												prod_categ = line.product_id.categ_id
												if prod_categ.Minimum_amount > 0 :
													price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
													if company_currency.id != web_currency.id:
														new_rate = (price*company_currency.rate)/web_currency.rate
													else:
														new_rate = price
													plus_points += int(new_rate / prod_categ.Minimum_amount)

								if plus_points > 0 :
									is_credit = loyalty_history_obj.search([('order_id','=',rec.id),('transaction_type','=','credit')])
									if is_credit:
										is_credit.write({
											'points': (plus_points),
											'state': 'done',
											'date' : datetime.now(),
											'partner_id': partner_id.id,
										})

										move.write({'loyalty_genrate':True ,'genrated_points':(move.genrated_points + plus_points)})

									else:
										vals = {
											'order_id':rec.id,
											'partner_id': partner_id.id,
											'loyalty_config_id' : con.id,
											'date' : datetime.now(),
											'transaction_type' : 'credit',
											'generated_from' : 'sale',
											'points': plus_points,
											'state': 'done',
										}
										loyalty_history = loyalty_history_obj.sudo().create(vals)
										move.write({'loyalty_genrate':True ,'genrated_points':plus_points})
										self.write({'loyalty_genrate':True ,'genrated_points':plus_points})
									rec.write({'order_credit_points':plus_points})

		if move.move_type == 'out_refund':
			sale_order = self.env['sale.order'].search([('name','=',move.invoice_origin)],limit=1)
			if sale_order:
				loyalty_history_obj = self.env['all.loyalty.history']   
				today_date = datetime.today().date()
				config = self.env['all.loyalty.setting'].sudo().search([('active','=',True),('issue_date', '<=', today_date ),
										('expiry_date', '>=', today_date )])
				if config : 
					for rec in sale_order:
						if move.genrated_points <= rec.partner_id.loyalty_pts:
							partner_id =rec.partner_id
							plus_points = 0.0

							company_currency = rec.company_id.currency_id
							web_currency = rec.pricelist_id.currency_id     
							
							if config.loyalty_basis_on == 'amount' :
								if config.loyality_amount > 0 :
									price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
									if company_currency.id != web_currency.id:
										new_rate = (price*company_currency.rate)/web_currency.rate
									else:
										new_rate = price
									plus_points =  int( new_rate / config.loyality_amount)

							if config.loyalty_basis_on == 'loyalty_category' :
								for line in  rec.order_line:
									if not line.discount_line or not line.is_delivery :
										if rec.is_from_website :
											prod_categs = line.product_id.public_categ_ids
											for c in prod_categs :
												if c.Minimum_amount > 0 :
													price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
													if company_currency.id != web_currency.id:
														new_rate = (price*company_currency.rate)/web_currency.rate
													else:
														new_rate = price
													plus_points += int(new_rate / c.Minimum_amount)
										else:
											prod_categ = line.product_id.categ_id
											if prod_categ.Minimum_amount > 0 :
												price = sum(rec.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))
												if company_currency.id != web_currency.id:
													new_rate = (price*company_currency.rate)/web_currency.rate
												else:
													new_rate = price
												plus_points += int(new_rate / prod_categ.Minimum_amount)
							
							if plus_points > 0 :
								is_credit = loyalty_history_obj.search([('order_id','=',rec.id),('transaction_type','=','credit')])
								if is_credit:
									is_credit.write({
										'points': - plus_points,
										'state': 'done',
										'date' : datetime.now(),
										'partner_id': partner_id.id,
									})
									move.write({'loyalty_genrate':False ,'genrated_points':move.genrated_points - plus_points})
								else:
									vals = {
										'order_id':rec.id,
										'partner_id': partner_id.id,
										'loyalty_config_id' : config.id,
										'date' : datetime.now(),
										'transaction_type' : 'credit',
										'generated_from' : 'sale',
										'points': -plus_points,
										'state': 'done',
									}
									if partner_id.loyalty_active:
										loyalty_history = loyalty_history_obj.sudo().create(vals)
										move.write({'loyalty_genrate':True ,'genrated_points':plus_points})
										self.write({'loyalty_genrate':True ,'genrated_points':plus_points})
								rec.write({'order_credit_points':plus_points})

	@api.depends('amount_residual', 'move_type', 'state', 'company_id', 'matched_payment_ids.state')
	def _compute_payment_state(self):
		stored_ids = tuple(self.ids)
		if stored_ids:
			# Flush models to ensure database consistency
			self.env['account.partial.reconcile'].flush_model()
			self.env['account.payment'].flush_model(['is_matched'])

			# Build SQL queries to get reconciliation information
			queries = []
			for source_field, counterpart_field in (
				('debit_move_id', 'credit_move_id'),
				('credit_move_id', 'debit_move_id'),
			):
				queries.append(SQL('''
					SELECT
						source_line.id AS source_line_id,
						source_line.move_id AS source_move_id,
						account.account_type AS source_line_account_type,
						ARRAY_AGG(counterpart_move.move_type) AS counterpart_move_types,
						COALESCE(BOOL_AND(COALESCE(pay.is_matched, FALSE))
							FILTER (WHERE counterpart_move.origin_payment_id IS NOT NULL), TRUE) AS all_payments_matched,
						BOOL_OR(COALESCE(BOOL(pay.id), FALSE)) as has_payment,
						BOOL_OR(COALESCE(BOOL(counterpart_move.statement_line_id), FALSE)) as has_st_line
					FROM account_partial_reconcile part
					JOIN account_move_line source_line ON source_line.id = part.%s
					JOIN account_account account ON account.id = source_line.account_id
					JOIN account_move_line counterpart_line ON counterpart_line.id = part.%s
					JOIN account_move counterpart_move ON counterpart_move.id = counterpart_line.move_id
					LEFT JOIN account_payment pay ON pay.id = counterpart_move.origin_payment_id
					WHERE source_line.move_id IN %s AND counterpart_line.move_id != source_line.move_id
					GROUP BY source_line.id, source_line.move_id, account.account_type
				''', SQL.identifier(source_field), SQL.identifier(counterpart_field), stored_ids))

			payment_data = defaultdict(list)
			for row in self.env.execute_query_dict(SQL(" UNION ALL ").join(queries)):
				payment_data[row['source_move_id']].append(row)
		else:
			payment_data = {}

		for invoice in self:
			if invoice.payment_state == 'invoicing_legacy':
				continue

			new_pmt_state = 'not_paid'

			currencies = invoice._get_lines_onchange_currency().currency_id
			currency = currencies if len(currencies) == 1 else invoice.company_id.currency_id
			reconciliation_vals = payment_data.get(invoice.id, [])
			payment_state_matters = invoice.is_invoice(True)

			if payment_state_matters:
				reconciliation_vals = [x for x in reconciliation_vals if x['source_line_account_type'] in ('asset_receivable', 'liability_payable')]

			if invoice.matched_payment_ids.filtered(lambda p: p.state == 'in_process' and p.amount != 0):
				new_pmt_state = invoice._get_invoice_in_payment_state()
				_logger.debug('In process payment detected, setting state to in_process with non-zero amount')
			elif currency.is_zero(invoice.amount_residual):
				if any(x['has_payment'] or x['has_st_line'] for x in reconciliation_vals):
					if all(x['all_payments_matched'] for x in reconciliation_vals):
						new_pmt_state = 'paid'
						if invoice.state != 'cancel':
							invoice.generate_loyalty_points(invoice)
						_logger.debug('Points added: all payments matched and residual zero')
					else:
						new_pmt_state = invoice._get_invoice_in_payment_state()
						if new_pmt_state == "paid" and invoice.state != 'cancel':
							invoice.generate_loyalty_points(invoice)
						_logger.debug('Points added in else condition for partially matched payments')
				else:
					new_pmt_state = 'in_payment' if invoice.matched_payment_ids.filtered(lambda p: p.state not in ['paid', 'reconciled']) else 'paid'
					if new_pmt_state == 'paid' and invoice.state != 'cancel':
						invoice.generate_loyalty_points(invoice)
						_logger.debug('Points added: fully paid with no pending payments')
			elif reconciliation_vals:
				new_pmt_state = 'partial'
				_logger.debug('Partial payment state assigned')
			elif invoice.matched_payment_ids.filtered(lambda p: p.state == 'paid'):
				new_pmt_state = invoice._get_invoice_in_payment_state()
				_logger.debug('Final paid state for matched payment')

			invoice.payment_state = new_pmt_state
