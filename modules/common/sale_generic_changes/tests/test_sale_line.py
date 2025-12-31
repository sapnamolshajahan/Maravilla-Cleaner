# -*- coding: utf-8 -*-
import logging

from odoo.tools import float_compare
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)

@tagged("common", "sale_generic_changes")
class TestSaleOrderLine(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 50.0,
            'is_storable': 'True',
            'qty_available': 5.0,
        })
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'WH1',
            'exclude_in_avail_stock': False,
        })
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 5.0,
        })
        self.sale_order = self.env['sale.order'].create({'partner_id': self.partner.id,'warehouse_id': self.warehouse.id})
        self.sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'price_unit': 100.0,
            'discount': 5.0,
            'product_uom_qty': 10.0,
        })

    def test_onchange_price_changed(self):
        # Verify initial state
        self.assertEqual(self.sale_order_line.price_unit, 100.0)
        self.assertEqual(self.sale_order_line.discount, 5.0)
        self.assertFalse(self.sale_order_line.price_changed)
        # Trigger onchange
        self.sale_order_line.price_changed = True
        self.sale_order_line.onchange_price_changed()
        # Verify original values are saved
        self.assertEqual(self.sale_order_line.price_unit_original, 100.0)
        self.assertEqual(self.sale_order_line.discount_original, 5.0)

    def test_compute_price_unit(self):
        # Case 1: price_changed is False
        self.sale_order_line.price_changed = False
        self.sale_order_line._compute_price_unit()
        self.assertEqual(
            self.sale_order_line.price_unit,
            self.product.list_price,
            "Price unit should use the default computation when price_changed is False."
        )
        # Case 2: price_changed is True
        self.sale_order_line.price_changed = True
        self.sale_order_line.price_unit_original = 150.0
        self.sale_order_line._compute_price_unit()
        self.assertEqual(
            self.sale_order_line.price_unit,
            150.0,
            "Price unit should match price_unit_original when price_changed is True."
        )

    def test_compute_discount_with_price_changed(self):
        self.sale_order_line.price_changed = True
        self.sale_order_line.discount_original = 15.0
        self.sale_order_line._compute_discount()
        self.assertEqual(
            self.sale_order_line.discount,
            15.0,
            "Discount should match discount_original when price_changed is True."
        )

    def test_compute_discount_without_price_changed(self):
        self.sale_order_line.price_changed = False
        self.sale_order_line.discount_original = 15.0
        self.sale_order_line._compute_discount()
        self.assertNotEqual(
            self.sale_order_line.discount,
            15.0,
            "Discount should not match discount_original when price_changed is False."
        )

    def test_compute_amount(self):
        self.env.company.sale_line_low_price_warning = True
        self.sale_order_line.price_unit = -1
        self.sale_order_line._compute_amount()
        # Calculate the expected price after discount
        calculated_price = self.sale_order_line.price_unit - (self.sale_order_line.price_unit * (self.sale_order_line.discount / 100))
        prec = self.env['decimal.precision'].precision_get('Product Price')
        self.assertTrue(
            float_compare(calculated_price, self.product.standard_price, precision_digits=prec) < 0,
            "The calculated price should be below the cost price to trigger the low margin warning."
        )

    def test_onchange_product_id_warning(self):
        """
        Test the low stock warning is triggered when product stock is insufficient.
        """
        # Call the onchange method
        self.company.sale_line_low_stock_warning = True
        self.company.sale_line_exclude_in_avail_stock = True
        self.sale_order_line._onchange_product_id_warning()
        # Assert that the stock fields are updated correctly
        self.assertEqual(self.sale_order_line.stock_available, 5.0,
                         "The stock available in the warehouse should be updated correctly.")
        self.assertEqual(self.sale_order_line.stock_available_all, 5.0,
                         "The stock available across all warehouses should be updated correctly.")
        # case2 sale_line_exclude_in_avail_stock is False
        self.company.sale_line_exclude_in_avail_stock = False
        self.sale_order_line._onchange_product_id_warning()
        # case3 sale_line_exclude_in_avail_stock is False and sale_line_exclude_in_avail_stock is true
        self.company.sale_line_low_stock_warning = False
        self.sale_order_line._onchange_product_id_warning()
        self.assertEqual(self.sale_order_line.stock_available, 5.0,
                         "The stock available in the warehouse should be updated correctly.")
        self.assertEqual(self.sale_order_line.stock_available_all, 5.0,
                         "The stock available across all warehouses should be updated correctly.")

    def test_get_display_price(self):
        """
        Test the _get_display_price method behavior based on the value of price_changed.
        """
        # Case 1: price_changed is True
        self.sale_order_line.price_changed = True
        self.sale_order_line.price_unit = 150.0
        display_price = self.sale_order_line._get_display_price()
        self.assertEqual(
            display_price,
            150.0,
            "The display price should match the price_unit when price_changed is True."
        )

    def test_get_stock_available(self):
        """
        Test the _get_stock_available method and the supporting stock calculation methods.
        """
        # Create additional warehouses
        warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Test Warehouse 2',
            'code': 'WH2',
            'exclude_in_avail_stock': False,
        })

        # Set up stock quants for product in both warehouses
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 10.0,
        })
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': warehouse_2.lot_stock_id.id,
            'quantity': 5.0,
        })
        # Create outgoing stock moves in warehouse 1
        self.env['stock.move'].create({
            'name':  self.product.name,
            'product_id': self.product.id,
            'warehouse_id': self.warehouse.id,
            'product_uom_qty': 4.0,
            'location_id': self.warehouse.lot_stock_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'state': 'assigned',
        })
        # Create outgoing stock moves in warehouse 2
        self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'warehouse_id': warehouse_2.id,
            'product_uom_qty': 3.0,
            'location_id': warehouse_2.lot_stock_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'state': 'assigned',
        })
        # Test the _get_stock_available method
        available_all, available_warehouse = self.sale_order_line._get_stock_available()
        # Calculate expected values
        expected_available_wh = 16  # Warehouse 1 on-hand minus outgoing
        expected_available_all = 13  # Total on-hand minus total outgoing
        # Assert the available stock values
        self.assertEqual(
            available_warehouse, expected_available_wh,
            "The available stock for the specific warehouse should be calculated correctly."
        )
        self.assertEqual(
            available_all, expected_available_all,
            "The available stock across all warehouses should be calculated correctly."
        )
        # Verify outgoing stock moves
        outgoing_all_moves, outgoing_all, outgoing_all_excl_this_line = \
            self.sale_order_line.outgoing_moves(self.sale_order_line, [self.warehouse, warehouse_2])
        self.assertEqual(outgoing_all, 7.0, "The total outgoing stock should match the created stock moves.")
        outgoing_wh_moves, outgoing_wh_qty, outgoing_wh_qty_excl_this_line = \
            self.sale_order_line.outgoing_wh_moves(self.sale_order_line)
        self.assertEqual(outgoing_wh_qty, 4.0,
                         "The outgoing stock for the specific warehouse should match the stock moves.")
