# -*- encoding: utf-8 -*-
from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    def _compute_override_supplier(self):
        for record in self:
            record.supplier_invoice_count = 0
            if not self.env.company.purchase_set_counts_zero:

                invoices = self.env['account.move'].sudo().search([('partner_id', '=', record.id),
                                                                   ('move_type', '=', 'in_invoice'),
                                                                   ('state', '=', 'posted')])
                record.supplier_invoice_count = len(invoices)


    def _compute_override_purchase(self):
        for record in self:
            record.purchase_order_count = 0
            if not self.env.company.purchase_set_counts_zero:
                purchase_orders = self.env['purchase.order'].sudo().search([('partner_id', '=', record.id)])
                record.purchase_order_count = len(purchase_orders)



    purchase_incoterm = fields.Many2one("account.incoterms", string="Default Purchase Incoterms")
    purchase_order_count = fields.Integer(string="# Purchases", compute="_compute_override_purchase")
    supplier_invoice_count = fields.Integer(string="# Supplier Invoices", compute="_compute_override_supplier")
    contact_sequence = fields.Integer(string="Sequence", default=0, required=False)
    type = fields.Selection(selection_add=[('purchase', 'Purchase')])

    def get_product_price(self, product, qty, uom=False, currency=False, zero_default_price=False):
        if not uom:
            uom = product.uom_id

        if not currency:
            currency = self.env.company.currency_id

        seller = product._select_seller(
            partner_id=self,
            quantity=qty,
            date=fields.Date.context_today(self),
            uom_id=uom)

        if not seller:
            if zero_default_price:
                return 0.0
            else:
                return self.env.company.currency_id.compute(product.standard_price, currency, round=False)
        else:
            price_unit = seller.price
            if seller.product_uom != uom:
                price_unit = seller.product_uom._compute_price(price_unit, uom)

            return seller.currency_id.compute(price_unit, currency, round=False)
