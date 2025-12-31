# -*- coding: utf-8 -*-
from odoo import models,fields


def _dont_count(ids):
    """Stub out costly count operations """
    result = {}
    for item_id in ids:
        result[item_id] = 0
    return result


class GenericViewProduct(models.Model):
    _inherit = "product.product"

    def _purchase_count(self):
        return _dont_count(self.ids)

    def _rules_count(self):
        return _dont_count(self.ids)

    def _sales_count(self):
        return _dont_count(self.ids)

    def _stock_move_count(self):
        result = {}
        for item_id in self.ids:
            result[item_id] = {
                "reception_count": 0,
                "delivery_count": 0,
            }
        return result


class GenericViewProductTemplate(models.Model):
    _inherit = "product.template"

    def _bom_orders_count(self):
        return _dont_count(self.ids)

    def _bom_orders_count_mo(self):
        return _dont_count(self.ids)

    def _purchase_count(self):
        return _dont_count(self.ids)

    def _rules_count(self):
        return _dont_count(self.ids)

    def _sales_count(self):
        return _dont_count(self.ids)

    """
    If no variants used, then just use the first product and get the free_qty from there
    """

    def _compute_free_qty(self):
        for record in self:
            product = record.product_variant_ids[0]
            record.free_qty = product.free_qty

    free_qty = fields.Float('Available ', compute='_compute_free_qty', compute_sudo=False)

