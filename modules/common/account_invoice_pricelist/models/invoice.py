# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.move"

    ################################################################################
    # Fields
    ################################################################################
    pricelist = fields.Many2one("product.pricelist", "Pricelist", help="Pricelist for current invoice.")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        result = super(AccountInvoice, self)._onchange_partner_id()
        for move in self:
            if move.partner_id:
                move.pricelist = move.partner_id.property_product_pricelist.id
        return result
