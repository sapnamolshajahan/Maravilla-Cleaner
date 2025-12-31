# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('common', 'mrp_lean')
class TestMrpBom(TransactionCase):
    def setUp(self):
        super(TestMrpBom, self).setUp()
        self.raw_material_product = self.env['product.product'].create({
            'name': 'Raw Material',
            'type': 'consu',
            'track_lean': True,
        })
        # Create finished product
        self.production_product = self.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
        })

        # Create Bill of Materials (BoM)
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.production_product.product_tmpl_id.id,
            'product_id': self.production_product.id,
            'company_id': self.env.company.id,
            'product_uom_id': self.env.ref('uom.product_uom_kgm').id,
            'bom_line_ids': [(0, 0, {
                'product_id': self.raw_material_product.id,
                'product_qty': 2.0,
            })]
        })

        # Create Manufacturing Order (MO)
        self.mrp_production = self.env['mrp.production'].create({
            'name': 'MO0001',
            'product_id': self.production_product.id,
            'bom_id': self.bom.id,
            'product_qty': 5.0,
            'product_uom_id': self.env.ref('uom.product_uom_kgm').id,
            'company_id': self.env.company.id,
            'state': 'confirmed',  # Should be in 'confirmed' or 'progress' for report inclusion
        })

        # Create Stock Move for raw materials
        self.stock_move = self.env['stock.move'].create({
            'name': 'Stock Move for MO',
            'product_id': self.raw_material_product.id,
            'product_uom_qty': 10.0,
            'raw_material_production_id': self.mrp_production.id,
            'state': 'done',
        })

    def test_mrp_production_product_report(self):
        """ Test if the MRP Production Product Report correctly includes manufacturing orders """
        # Fetch the report data
        report = self.env['mrp.production.product.report'].search([
            ('name', '=', self.mrp_production.name)
        ])
        self.assertTrue(report, "Report entry should exist for the manufacturing order")
        self.assertEqual(report.production_product_id, self.production_product, "Finished product should match")
        self.assertEqual(report.raw_material_product_id, self.raw_material_product, "Raw material should match")
        self.assertEqual(report.production_state, 'confirmed', "MO state should be 'confirmed'")
