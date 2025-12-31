# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase, tagged
from datetime import datetime

_logger = logging.getLogger(__name__)


@tagged("common", "purchase_update_linked_sol")
class TestPurchaseOrder(TransactionCase):

    def setUp(self):
        super(TestPurchaseOrder, self).setUp()

        self.currency_nzd = self.env['res.currency'].create({
            'name': 'NN',
            'symbol': '$',
            'rate': 1.0,
        })

        self.currency_usd = self.env['res.currency'].sudo().create({
            'name': 'TT',
            'symbol': '^',
            'rate_ids': [(0, 0, {
                'rate': 0.75,
                'company_id': self.env.company.id,
                'name': datetime.now(),
            })],
        })

        self.supplier = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })

        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'currency_id': self.currency_nzd.id,
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'seller_ids': [(0, 0, {
                'partner_id': self.supplier.id,
                'min_qty': 1,
                'price': 10.0,
            })],
        })

        self.product_supplier = self.env['product.supplierinfo'].create({
            'product_id': self.product.id,
            'partner_id': self.supplier.id,
            'price': 10.0,
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'company_id': self.company.id,
            'currency_id': self.currency_nzd.id,
        })

        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'company_id': self.company.id,
            'currency_id': self.currency_usd.id,
        })

        self.sale_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
            'purchase_order': self.purchase_order.id
        })


    def test_calculate_unit_price(self):
        """Test the calculation of unit price in the company's default currency."""
        po_line = self.env['purchase.order.line'].create({
            'order_id': self.purchase_order.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 20.0,
        })

        purchase_price = self.purchase_order.calculate_unit_price(po_line)
        self.assertEqual(round(purchase_price, 2), 26.67, "Unit price in NZD should be calculated correctly.")

    def test_write_updates_sale_line(self):
        """Test that updating purchase order line updates the related sale order line."""
        po_line = self.env['purchase.order.line'].create({
            'order_id': self.purchase_order.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 20.0,
            'sale_line_id': self.sale_line.id,
        })

        po_line.write({'price_unit': 25.0})

        self.assertEqual(self.sale_line.purchase_price, 33.33, "Sale line purchase price should be updated.")
        self.assertEqual(self.sale_line.purchase_order.id, self.purchase_order.id, "Sale line should link to the purchase order.")

    def test_prepare_purchase_order_line_from_procurement(self):
        """Test the procurement logic for creating purchase order lines."""
        values = {'sale_line_id': self.sale_line.id,
                  'supplier': self.product_supplier}
        po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
            self.product,
            5,
            self.product.uom_po_id,
            self.env.ref('stock.stock_location_customers'),
            'Test Procurement',
            'SO001',
            self.company,
            values,
            self.purchase_order,
        )

        po_line = self.env['purchase.order.line'].create(po_line_vals)


        self.assertEqual(po_line.sale_line_id.id, self.sale_line.id,
                         "Sale line ID should be set on the purchase order line.")
        self.assertEqual(self.sale_line.purchase_order.id, self.purchase_order.id,
                         "Sale line should link to the purchase order.")
