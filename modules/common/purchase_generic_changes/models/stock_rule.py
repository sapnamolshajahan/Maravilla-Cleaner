# -*- encoding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_compare, frozendict, split_every


class GenericStockRule(models.Model):
    _inherit = 'stock.rule'

    ###########################################################################
    # Fields
    ###########################################################################

    ###########################################################################
    # Model methods
    ###########################################################################
    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(GenericStockRule, self)._prepare_purchase_order(company_id, origins, values)
        res['date_order'] = fields.Date.today()
        return res


class StockOrderPoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def _get_product_context(self):
        """Allows future dates moves from purchase orders to be included in available so don't reorder again."""

        res = super(StockOrderPoint, self)._get_product_context()
        if res.get('to_date'):
            res.pop('to_date')
        return res
