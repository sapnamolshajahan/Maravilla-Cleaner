# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleReport(models.Model):
    """
    Tweak sales report to include product analysis
    """
    _inherit = "sale.report"

    ################################################################################
    # Fields
    ################################################################################
    product_analysis = fields.Many2one("product.analysis.type", string="Analysis Type")

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['product_analysis'] = "t.product_analysis"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """, t.product_analysis"""
        return res
