# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_analysis = fields.Many2one(comodel_name="product.analysis.type", string="Analysis Type",
                                       related='product_id.product_analysis', store=True)
