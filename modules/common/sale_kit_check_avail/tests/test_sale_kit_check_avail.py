# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSaleOrderLineComputeUomQty(TransactionCase):

    def setUp(self):
        super(TestSaleOrderLineComputeUomQty, self).setUp()
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TW',
        })
        self.product_component = self.env['product.product'].create({
            'name': 'Component Product',
            'type': 'consu',
            'is_storable':True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.product_finished = self.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
            'is_storable': True,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_finished.product_tmpl_id.id,
            'type': 'phantom',
            'bom_line_ids': [(0, 0, {
                'product_id': self.product_component.id,
                'product_qty': 2.0,
            })],
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'warehouse_id': self.warehouse.id,
        })

    def test_compute_product_uom_qty_sufficient_inventory(self):
        """Test _compute_product_uom_qty with sufficient inventory."""
        self.env['stock.quant'].create({
            'product_id': self.product_component.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 10,
        })
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_finished.id,
            'product_uom_qty': 2,
        })
        sale_order_line._compute_product_uom_qty()
        self.assertTrue(sale_order_line, "Sale order line should be created successfully with sufficient inventory.")

    def test_compute_product_uom_qty_insufficient_inventory(self):
        """Test _compute_product_uom_qty with insufficient inventory."""
        self.env['stock.quant'].create({
            'product_id': self.product_component.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 2,
        })
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_finished.id,
            'product_uom_qty': 2,
        })
        with self.assertRaises(ValidationError):
            sale_order_line._compute_product_uom_qty()
