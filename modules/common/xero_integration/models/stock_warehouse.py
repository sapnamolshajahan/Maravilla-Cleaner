import logging

from odoo import models, fields, api,_
_logger = logging.getLogger(__name__)


class StockWarehouseDefaultTag(models.Model):
    _inherit = 'stock.warehouse'

    default_analytic_account = fields.Many2one(string='Default Analytic Account',
                                               comodel_name='account.analytic.account')

    def get_default_analytic_account(self):
        return self.default_analytic_account and self.default_analytic_account.id
