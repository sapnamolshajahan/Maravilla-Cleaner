# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo import fields
import datetime


@tagged('common', 'operations_stocktake cyclic')
class TestProductCyclicCount(TransactionCase):
    def setUp(self):
        super(TestProductCyclicCount, self).setUp()
        self.cyclic_count = self.env['product.cyclic.count'].create({
            'name': 'Test Count',
            'frequency': 2,
            'time_measure': '7',  # Weekly
            'last_count_date': fields.Date.today(),
        })
        self.product1 = self.env['product.template'].create({'name': 'Product 1', 'type': 'consu', 'is_storable': True})
        self.product2 = self.env['product.template'].create({'name': 'Product 2', 'type': 'consu', 'is_storable': True})
        self.cyclic_count.product_ids = [(4, self.product1.id), (4, self.product2.id)]

    def test_cron_product_cyclic_count(self):
        """Test cyclic count updates correctly"""
        self.cyclic_count._cron_product_cyclic_count()
        self.assertIsNotNone(self.cyclic_count.next_count_date, "Next count date should be calculated")

        expected_next_date = fields.Date.today() + datetime.timedelta(
            days=int(self.cyclic_count.time_measure) * self.cyclic_count.frequency)
        self.assertEqual(self.cyclic_count.next_count_date, expected_next_date,
                         "Next count date calculation is incorrect")

    def test_stock_quant_update(self):
        """Test that stock quants are correctly updated or created"""
        warehouse = self.env.ref('stock.warehouse0')
        warehouse.write({'incl_cyclic': True})
        location = warehouse.lot_stock_id
        self.cyclic_count._cron_product_cyclic_count()
        product_product = self.env['product.product'].search(
            [('product_tmpl_id', 'in', [self.product1.id, self.product2.id])])
        quants = self.env['stock.quant'].search(
            [('location_id', '=', location.id), ('product_id', 'in', product_product.ids)])
        self.assertTrue(quants, "Stock quants should be created or updated for cyclic count products")
        for quant in quants:
            self.assertEqual(quant.inventory_date, self.cyclic_count.cycle_end_date,
                             "Inventory date should match cycle end date")

    def test_stock_quant_update_with_quant(self):
        """Test that stock quants are correctly updated or created"""
        warehouse = self.env.ref('stock.warehouse0')
        warehouse.write({'incl_cyclic': True})
        location = warehouse.lot_stock_id
        self.env['stock.quant'].create([{
            'product_id': self.env['product.product'].search([('product_tmpl_id', 'in', [self.product1.id])]).id,
            'location_id': location.id,
            'quantity': 2.0,
            'cyclic': True,
        }, {
            'product_id': self.env['product.product'].search([('product_tmpl_id', 'in', [self.product1.id])]).id,
            'location_id': location.id,
            'quantity': 2.0,
            'cyclic': True,
        }]
        )
        self.cyclic_count._cron_product_cyclic_count()
        product_product = self.env['product.product'].search(
            [('product_tmpl_id', 'in', [self.product1.id, self.product2.id])])
        quants = self.env['stock.quant'].search(
            [('location_id', '=', location.id), ('product_id', 'in', product_product.ids)])
        self.assertTrue(quants, "Stock quants should be updated for cyclic count products")
        for quant in quants:
            self.assertEqual(quant.inventory_date, self.cyclic_count.cycle_end_date,
                             "Inventory date should match cycle end date")
