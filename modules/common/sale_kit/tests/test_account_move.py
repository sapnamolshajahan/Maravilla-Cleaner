# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestAngloSaxonPriceUnit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAngloSaxonPriceUnit, cls).setUpClass()

        # Create a product with a standard price
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
            'standard_price': 50.0,
        })

        # Create a phantom BOM for the product
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'type': 'phantom',
            'bom_line_ids': [],
        })

        # Create a sale order line to link stock moves
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.env.ref('base.res_partner_1').id,
        })

        cls.sale_order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        })

        # Create stock moves linked to the sale order line
        cls.stock_move_1 = cls.env['stock.move'].create({
            'name': 'Test Move 1',
            'product_id': cls.product.id,
            'product_uom_qty': 2,
            'price_unit': 60.0,
            'sale_line_id': cls.sale_order_line.id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            'state': 'done',
        })

        cls.stock_move_2 = cls.env['stock.move'].create({
            'name': 'Test Move 2',
            'product_id': cls.product.id,
            'product_uom_qty': 3,
            'price_unit': 70.0,
            'sale_line_id': cls.sale_order_line.id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id,
            'state': 'done',
        })

        # Create an invoice line (account.move.line)
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.env.ref('base.res_partner_1').id,
        })

        cls.invoice_line = cls.env['account.move.line'].create({
            'move_id': cls.invoice.id,
            'product_id': cls.product.id,
            'quantity': 5,  # Same as total stock_move quantities (2+3)
            'price_unit': 100.0,
            'stock_move_id': cls.stock_move_1.id,  # Link to one of the stock moves
        })

    def test_anglo_saxon_price_unit_with_phantom_bom(self):
        price_unit = self.invoice_line._stock_account_get_anglo_saxon_price_unit()

        # Expected cost calculation: (2*60 + 3*70) / 5 = (120 + 210) / 5 = 330 / 5 = 66
        expected_price_unit = 66.0
        self.assertAlmostEqual(price_unit, expected_price_unit, places=2, msg="Price unit calculation incorrect")

