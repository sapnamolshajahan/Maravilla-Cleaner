from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError, ValidationError

class ResCompany(models.Model):
	_inherit = 'res.company'

	allow_prezzy_redemption = fields.Boolean('Allow Prezzy card redemption', default=False)
	disallow_overdue = fields.Boolean('Disallow Points for Overdue Payments', default=False)
