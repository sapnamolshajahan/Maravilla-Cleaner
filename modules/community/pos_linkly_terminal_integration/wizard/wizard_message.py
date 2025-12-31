# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api, fields, models, _

class LinklyWizardMessage(models.TransientModel):
	_name = "linkly.wizard.message"
	_description = "EFTPOS Message Wizard"

	text = fields.Text(string='Message')

	@api.model
	def genrated_message(self,message,name='Message/Summary'):
		res = self.create({'text': message})
		return {
			'name'     : name,
			'type'     : 'ir.actions.act_window',
			'res_model': 'linkly.wizard.message',
			'view_mode': 'form',
			'target'   : 'new',
			'res_id'   : res.id,
		}
