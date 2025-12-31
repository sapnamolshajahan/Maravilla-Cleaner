# -*- coding: utf-8 -*-
from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def calculate_unit_price(self, line):
        default_currency = self.env.company.currency_id.id
        purchase_price = line.price_unit
        if line.order_id.currency_id.id != default_currency:
            purchase_price = line.price_unit / line.order_id.currency_id.rate
        # returns in NZD
        return purchase_price


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def write(self, values):
        res = super(PurchaseOrderLine, self).write(values)
        for line in self:
            purchase_price = line.order_id.calculate_unit_price(line)
            if line.sale_line_id:
                if (line.sale_line_id.order_id.currency_id and line.sale_line_id.order_id.currency_id.id !=
                        self.env.company.currency_id.id):
                    purchase_price = line.sale_line_id.order_id.currency_id.rate * purchase_price
                line.sale_line_id.write({"purchase_price": purchase_price})
                if not line.sale_line_id.purchase_order:
                    line.sale_line_id.purchase_order = line.order_id.id
        return res

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, location_dest_id,
                                                      name, origin, company_id, values, po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, po)
        if self.env.context.get('sale_line_id', None):
            res['sale_line_id'] = self.env.context['sale_line_id']
            values['sale_line_id'] = self.env.context['sale_line_id']
            order_line = self.env['sale.order.line'].browse(self.env.context['sale_line_id'])
            order_line.purchase_order = po.id
        return res
