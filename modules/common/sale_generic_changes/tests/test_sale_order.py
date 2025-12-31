# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


@tagged("common", "sale_generic_changes")
class TestSaleOrder(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Create the required records for testing
        self.partner = self.env.ref('base.partner_demo')
        self.product = self.env.ref('product.product_product_1')
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'price_unit': 100.0,
            })]
        })
        # Adding an invoice address
        self.sale_order.partner_invoice_id = self.partner.id

    def test_action_sale_order_set_invoiced(self):
        # Test invoicing a sale order
        self.sale_order.action_sale_order_set_invoiced()
        self.assertEqual(self.sale_order.invoice_status, 'invoiced')
        # Test trying to invoice multiple orders
        sale_orders = self.env['sale.order'].create([{
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'price_unit': 100.0,
            })]
        }, {
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'price_unit': 100.0,
            })]
        }])
        with self.assertRaises(UserError):
            sale_orders.action_sale_order_set_invoiced()

    def test_action_confirm(self):
        # Test confirming a sale order and ensuring line sequence is set
        self.sale_order.action_confirm()
        self.assertTrue(all(line.sequence > 0 for line in self.sale_order.order_line))

    def test_action_recalculate_stock(self):
        # Test recalculating stock for sale order
        self.sale_order.action_recalculate_stock()
        for line in self.sale_order.order_line:
            self.assertIsNotNone(line.stock_available)
            self.assertIsNotNone(line.stock_available_all)
        self.env.company.sale_line_exclude_in_avail_stock = True
        self.sale_order.action_recalculate_stock()



    def test_get_invoiceable_lines(self):
        # Set up a Sale Order with mixed line types (product, service, downpayment)
        service_product = self.env['product.product'].create({
            'name': 'Consultancy',
            'type': 'service',
        })
        self.product.type = 'consu'
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
                'price_unit': 100.0,
            }), (0, 0, {
                'product_id': service_product.id,
                'product_uom_qty': 5,
                'qty_invoiced': 2,
                'price_unit': 50.0,
            }), (0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3,
                'is_downpayment': True,
                'price_unit': 0.0,
            })],
        })
        self.env.context = dict(self.env.context, advance_invoice=True)
        self.env.company.advance_invoice_rule = True
        with self.assertRaises(UserError):
            sale_order._get_invoiceable_lines()
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        self.assertTrue(picking, "No picking created for the sale order")
        picking.move_line_ids.quantity = 10  # Fully deliver the consumable product
        picking.button_validate()
        self.env.context = dict(self.env.context, advance_invoice=True)
        invoiceable_lines = sale_order._get_invoiceable_lines(final=True)
        self.assertEqual(len(invoiceable_lines), 3,
                         "Expected 3 invoiceable lines (service, product, and down payment)")
        # Check qty_to_invoice for service and consumable lines
        for line in invoiceable_lines:
            if line.product_id.type == 'service':
                self.assertEqual(line.qty_to_invoice, line.product_uom_qty - line.qty_invoiced,
                                 "Incorrect qty_to_invoice for service line")
            elif line.product_id.type == 'consu' and not line.is_downpayment:
                self.assertEqual(line.qty_to_invoice, line.qty_delivered - line.qty_invoiced,
                                 "Incorrect qty_to_invoice for consumable line")
        # Check qty_to_invoice for down payment
        down_payment_line = sale_order.order_line.filtered(lambda l: l.is_downpayment)
        self.assertTrue(down_payment_line, "Down payment line not found")
        self.assertEqual(down_payment_line.qty_to_invoice,
                         down_payment_line.product_uom_qty - down_payment_line.qty_invoiced,
                         "Incorrect qty_to_invoice for down payment line")

    def test_action_set_prices(self):
        # Test setting prices for sale order lines
        self.sale_order.action_set_prices()
        for line in self.sale_order.order_line:
            self.assertTrue(line.price_changed)
            self.assertEqual(line.discount_original, line.discount)
            self.assertEqual(line.price_unit_original, line.price_unit)

    def test_calc_invoice_status(self):
        # Test cleaning up the invoice status on sale orders
        self.sale_order.state = 'sent'
        for line in self.sale_order.order_line:
            line.qty_invoiced = line.product_uom_qty
        self.sale_order.invoice_status = 'to invoice'
        self.sale_order.calc_invoice_status()
        self.assertEqual(self.sale_order.invoice_status, 'invoiced')

    def test_action_sort_lines(self):
        # Test sorting the lines in the sale order
        result = self.sale_order.action_sort_lines()
        self.assertEqual(result['name'], 'Sale Line Sort')

    def test_action_force_warehouse(self):
        # Test forcing the warehouse on sale order lines
        new_warehouse = self.env.ref('stock.warehouse0')  # Adjust to an actual warehouse
        self.sale_order.warehouse_id = new_warehouse
        self.sale_order.action_force_warehouse()
        for line in self.sale_order.order_line:
            self.assertEqual(line.warehouse_id, new_warehouse)
        self.sale_order.state = 'sale'
        with self.assertRaises(UserError):
            self.sale_order.action_force_warehouse()
