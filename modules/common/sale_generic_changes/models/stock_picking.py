# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    @api.depends("sale_id")
    def _sales_count(self):
        for r in self:
            r.sales_count = 1 if r.sale_id else 0

    ###########################################################################
    # Fields
    ###########################################################################
    sales_count = fields.Integer(string="No. of sale orders related", compute="_sales_count")

    def action_view_sale_orders(self):
        u"""
        This function returns an action that display existing sale orders of given picking ids (self).
        It can either be a in a list or in a form view, if there is only one delivery order to show.
        """
        sale_ids = self.mapped('sale_id')

        result = {
            'name': 'Sale Orders',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('sale.view_order_tree').id, 'list'), (self.env.ref('sale.view_order_form').id, 'form')],
            'target': 'main',
            'context': self.env.context,
            'res_model': 'sale.order',
        }

        # Go to sale orders tree view
        if len(sale_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % sale_ids.ids

        # Go to sale order form
        elif len(sale_ids) == 1:
            result['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            result['res_id'] = sale_ids.ids[0]

        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


class StockMove(models.Model):
    _inherit = 'stock.move'

    # in some cases a stock move will have both a SOL and a POL and the SOL is getting called last
    # so we check if from vendor and set the POL

    def _get_source_document(self):
        res = super()._get_source_document()
        if self.purchase_line_id and self.location_id.usage == 'supplier':
            return self.purchase_line_id.order_id
        else:
            return res





