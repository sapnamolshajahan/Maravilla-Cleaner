from odoo import models,fields

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    x_timer_start = fields.Datetime()
    x_timer_stop = fields.Datetime()
