from odoo import api, fields, Command, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    default_payment_mode = fields.Selection(selection=
        [('own_account', 'Employee (to reimburse)'),
         ('company_account', 'Company')],
        string="Default Payment Mode for Expenses",
        default='company_account'
    )

