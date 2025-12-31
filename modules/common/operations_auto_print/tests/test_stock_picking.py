# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo import fields

@tagged('common','operations_auto_print')
class TestStockPicking(TransactionCase):

    def setUp(self):
        super(TestStockPicking, self).setUp()
        self.warehouse = self.env["stock.warehouse"].browse(self.ref('stock.warehouse0'))
        self.picking_type = self.env["stock.picking.type"].create({
            "name": "Test Picking Type",
            "warehouse_id": self.warehouse.id,
            "code": "outgoing",
            'sequence_code': 'PT',
            'create_backorder':'never'
        })
        self.picking = self.env["stock.picking"].create({
            "name": "Test Picking",
            "partner_id": self.ref('base.res_partner_12'),
            "picking_type_id": self.picking_type.id,
            "state": "done",
            "location_id": self.ref('stock.stock_location_stock'),
            "location_dest_id": self.ref('stock.stock_location_stock')
        })
        self.picking_line = self.env["stock.move"].create({
            'name':'Demo move',
            "product_id": self.ref('product.product_product_12'),
            "product_uom_qty": 4,
            "quantity": 1,
            "picking_id": self.picking.id,
            "location_id": self.ref('stock.stock_location_stock'),
            "location_dest_id": self.ref('stock.stock_location_stock')
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'order_line': [
                fields.Command.create({
                    'product_id': self.ref('product.product_product_12'),
                    'product_uom_qty': 1,
                    'price_unit': 100,
                })
            ],
        })
        self.sale_order.warehouse_id.picking_printer = 'Test Printer'

    def test_queue_packing_report(self):
        """
        Test `queue_packing_report` when no packing printer is configured.
        """
        self.warehouse.packing_printer = "TestPrinter"
        self.picking.button_validate()
        self.assertTrue(not self.picking.printed, "The picking should be queued for auto-print.")

    def test_allow_packing_print(self):
        """
        Test the `allow_packing_print` method.
        """
        self.picking.with_context(cancel_backorder=False).button_validate()
        self.assertTrue(self.picking.allow_packing_print())
        self.picking.picking_type_id.code = "incoming"
        self.assertFalse(self.picking.allow_packing_print())
        self.picking.state = "cancel"
        self.assertFalse(self.picking.allow_packing_print())

    def test_allow_picking_print(self):
        """
        Test the allow_picking_print method logic.
        """
        self.assertTrue(self.picking.allow_picking_print())
        self.picking.state = "cancel"
        self.assertFalse(self.picking.allow_picking_print())

    def test_action_confirm_triggers_picking_auto_print(self):
        """Test that confirming a sale order triggers the picking auto-print."""
        self.assertFalse(self.sale_order.picking_ids, "There should be no pickings before order confirmation.")
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids, "A picking should be created after order confirmation.")
        picks_to_print = self.sale_order.picking_ids.filtered(lambda r: not r.printed)
        self.assertTrue(picks_to_print, "The picking should be queued for auto-print.")