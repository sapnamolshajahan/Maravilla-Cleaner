# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "sale_generic_changes")
class TestStockPicking(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_12')
        self.sale_order = self.env.ref('sale.sale_order_1')
        self.stock_picking = self.env.ref('stock.outgoing_shipment_main_warehouse')

    def test_sales_count_computation(self):
        self.stock_picking.sale_id = False
        # After unlinking sale_order, sales_count should be 0
        self.assertEqual(self.stock_picking.sales_count, 0, "Sales count should be 0 when sale_id is removed.")
        # Link back the sale order
        self.stock_picking.sale_id = self.sale_order.id
        # The sales_count should again be 1
        self.assertEqual(self.stock_picking.sales_count, 1, "Sales count should be 1 when sale_id is set again.")

    def test_action_view_sale_orders(self):
        self.stock_picking.sale_id = self.sale_order.id
        action = self.stock_picking.action_view_sale_orders()
        self.assertEqual(action['res_model'], 'sale.order')
        # If there is one sale order, check if it opens the form view
        self.assertEqual(action['views'][0][1], 'form', "The view should be a form view for a single sale order.")
        self.assertEqual(action['res_id'], self.sale_order.id, "The form view should open for the linked sale order.")
        # Check when there are no sale orders
        self.stock_picking.sale_id = False
        action = self.stock_picking.action_view_sale_orders()
        self.assertEqual(action['type'], 'ir.actions.act_window_close',
                         "The action should close the window if no sale orders are linked.")
