# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase,tagged

@tagged('common','product_pricelist_decimal_precision')
class TestPurchaseOrderLinePrecision(TransactionCase):

    def setUp(self):
        super(TestPurchaseOrderLinePrecision, self).setUp()
        self.purchase_order_line_model = self.env['purchase.order.line']
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test Tax 10%',
            'amount': 10,
            'price_include': False,
        })
        self.tax_included = self.env['account.tax'].create({
            'name': 'Test Tax Included',
            'amount': 15,
            'price_include': True,
        })
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })
        self.purchase_order_line = self.purchase_order_line_model.create({
            'order_id':self.purchase_order.id,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'price_unit': 100.0,
        })
        self.different_uom = self.env['uom.uom'].create({
            'name': 'Custom UOM',
            'category_id': self.product.uom_id.category_id.id,
            'factor_inv': 2.0,
            'uom_type': 'smaller',
        })

    def test_get_stock_move_price_unit_no_taxes(self):
        price_unit = self.purchase_order_line._get_stock_move_price_unit()
        self.assertEqual(price_unit, 100.0, "Price unit should match the line's price_unit")
        self.purchase_order_line.product_uom = self.different_uom.id
        price_unit = self.purchase_order_line._get_stock_move_price_unit()
        self.assertEqual(price_unit, 50, "Price unit should remain unchanged with different UOMs")
        self.purchase_order_line.product_uom = self.product.uom_id.id
        self.purchase_order_line.taxes_id = [(4, self.tax_included.id)]
        price_unit = self.purchase_order_line._get_stock_move_price_unit()
        self.assertEqual(price_unit, 100.0, "Price unit should remain unchanged for price-included tax")
        self.purchase_order_line.taxes_id = [(4, self.tax.id)]
        price_unit = self.purchase_order_line._get_stock_move_price_unit()
        self.assertEqual(price_unit, 100.0, "Price unit should remain unchanged for non-price-included tax")


    def test_get_price_unit(self):
        """Test the _get_price_unit method in StockMove."""
        stock_move = self.env['stock.move'].create({
            'name': 'Test Stock Move',
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'purchase_line_id': self.purchase_order_line.id,
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_output'),
        })
        price_unit = stock_move._get_price_unit()
        self.assertEqual(price_unit[self.env['stock.lot']], 100.0,
                         "Price unit should match the purchase line's price_unit when no taxes are applied.")
        self.purchase_order_line.product_uom = self.different_uom
        price_unit = stock_move._get_price_unit()
        self.assertEqual(price_unit[self.env['stock.lot']],
                         100.0 * (self.different_uom.factor / self.product.uom_id.factor),
                         "Price unit should remain unchanged when the purchase order line uses a different UOM.")
        self.purchase_order_line.product_uom = self.product.uom_id.id
        self.purchase_order_line.taxes_id = [(4, self.tax_included.id)]
        price_unit = stock_move._get_price_unit()
        self.assertEqual(price_unit[self.env['stock.lot']], 100.0,
                         "Price unit should remain unchanged when a price-included tax is applied.")
        self.purchase_order_line.taxes_id = [(4, self.tax.id)]
        price_unit = stock_move._get_price_unit()
        self.assertEqual(price_unit[self.env['stock.lot']], 100.0,
                         "Price unit should remain unchanged when a non-price-included tax is applied.")

