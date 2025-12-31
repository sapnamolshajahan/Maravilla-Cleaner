# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _, tools
from datetime import date, time, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
import logging
import math
from odoo.http import request

_logger = logging.getLogger(__name__)
	

class web_category(models.Model):
	_inherit = 'product.public.category'

	Minimum_amount  = fields.Integer("Amount For loyalty Points")
	amount_footer = fields.Integer('Amount', related='Minimum_amount')


class ResConfigSettings_Inherit(models.TransientModel):
	_inherit = 'res.config.settings'

	allow_to_loyalty = fields.Boolean('Allow Loyalty Points',related="website_id.allow_to_loyalty",readonly=False)
	allow_prezzy_redemption = fields.Boolean('Allow Prezzy card redemption',
											 default=lambda self: self.env.company.allow_prezzy_redemption)
	disallow_overdue = fields.Boolean('Disallow Points for Overdue Payments',
									  default=lambda self: self.env.company.disallow_overdue)

	def set_values(self):
		super(ResConfigSettings_Inherit, self).set_values()
		self.env.company.write(
			{
				"allow_prezzy_redemption": self.allow_prezzy_redemption,
				"disallow_overdue": self.disallow_overdue,
			}
		)

	
class Website(models.Model):
	_inherit = 'website'
		
	allow_to_loyalty = fields.Boolean('Allow Loyalty Points')


	def get_loyalty_balance(self,order): 
		today_date = datetime.today().date() 
		amt_total = order.amount_total
		partner_id =order.partner_id
		loyalty_pts = 0.0
		plus_points = 0.0
		total_loyalty = 0.0
		company_currency = self.company_id.currency_id
		web_currency = self.pricelist_id.currency_id

		order.write({'is_from_website': True})

		config = self.env['all.loyalty.setting'].search([('multi_company_ids','in',self.company_id.id),('active','=',True),('issue_date', '<=', today_date ),
							('expiry_date', '>=', today_date )])
		
		path = request.httprequest.full_path
		show_redeem = True
		
		if config : 
			if config.loyalty_basis_on == 'amount' :
				if config.loyality_amount > 0 :
					price = sum(order.order_line.filtered(lambda x: not x.is_delivery).mapped('price_total'))	
					if company_currency.id != web_currency.id:
						new_rate = (price*company_currency.rate)/web_currency.rate
					else:
						new_rate = price
					plus_points =  int( new_rate / config.loyality_amount )
					total_loyalty = partner_id.loyalty_pts + plus_points

			if config.loyalty_basis_on == 'loyalty_category' :
				for line in  order.order_line:
					if not line.is_delivery :
						prod_categs = line.product_id.public_categ_ids
						for c in prod_categs :
							if c.Minimum_amount > 0 :
								if company_currency.id != web_currency.id:
									price = line.price_total
									new_rate = (price*company_currency.rate)/web_currency.rate
								else:
									new_rate = line.price_total
								plus_points += int(new_rate / c.Minimum_amount)

				total_loyalty = partner_id.loyalty_pts + plus_points

			if "/shop/confirmation" in str(path) :
				total_loyalty = partner_id.loyalty_pts 
				show_redeem = False

			total_loyalty -= order.order_redeem_points

		if total_loyalty <= 0.0:
			show_redeem = False

		return [plus_points,total_loyalty,show_redeem]
			

		
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
