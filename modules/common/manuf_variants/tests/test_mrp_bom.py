# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo import fields
from odoo.exceptions import ValidationError


@tagged('common', 'manuf_variants')
class TestMrpBom(TransactionCase):
    def setUp(self):
        super(TestMrpBom, self).setUp()
        self.product1 = self.env.ref('product.product_product_5')
        self.product2 = self.env.ref('product.product_product_6')
        self.product3 = self.env.ref('product.product_product_4_product_template')
        self.bom_model = self.env['mrp.bom']
        self.product1.product_tmpl_id.write({
            'is_intermediate': True
        })
        self.product2.product_tmpl_id.write({
            'is_intermediate': True
        })

        self.fp_bom = self.bom_model.create([
            {'product_tmpl_id': self.product3.id}
        ])
        self.intermediate_bom = self.bom_model.create([
            {
                'product_tmpl_id': self.product1.product_tmpl_id.id,
                'product_id': self.product1.id,
                'fp_bom_id': self.fp_bom.id
            },
            {
                'product_tmpl_id': self.product2.product_tmpl_id.id,
                'product_id': self.product2.id
            }
        ])

    def test_create_intermediate_bom(self):
        for rec in self.intermediate_bom:
            self.assertFalse(rec.product_id)

    def test_compute_possible_product_template_attribute_value_ids(self):
        self.intermediate_bom._compute_possible_product_template_attribute_value_ids()
        for bom in self.intermediate_bom:
            if bom.fp_bom_id:
                self.assertTrue(bom.possible_product_template_attribute_value_ids)

    def test_check_bom_lines(self):
        variant1 = self.fp_bom.possible_product_template_attribute_value_ids[0]
        with self.assertRaises(ValidationError):
            self.fp_bom.write({
                'product_id': self.env['product.product'].search([('product_tmpl_id', '=', self.product3.id)], limit=1),
                'bom_line_ids': [
                    fields.Command.create({
                        'product_id': self.env.ref('product.product_product_6').id,
                        'product_qty': 2.0,
                        'bom_product_template_attribute_value_ids': [
                            fields.Command.link(variant1.id)  # Add variant 1
                        ]
                    })
                ]
            })

        with self.assertRaises(ValidationError):
            self.fp_bom.write({
                'byproduct_ids': [
                    fields.Command.create({
                        'product_id': self.env['product.product'].search([('product_tmpl_id', '=', self.product3.id)],
                                                                         limit=1).id,

                    })
                ]
            })

        with self.assertRaises(ValidationError):
            self.fp_bom.write({
                'product_id': False,
                'is_intermediate': True,
                'bom_line_ids': [
                    fields.Command.create({
                        'product_id': self.env.ref('product.product_product_6').id,
                        'product_qty': 2.0,
                        'bom_product_template_attribute_value_ids': [
                            fields.Command.link(variant1.id)
                        ]
                    })
                ]
            })

        self.product2.product_tmpl_id.write({
            'is_intermediate': False
        })

        with self.assertRaises(ValidationError):
            self.fp_bom.write({
                'product_tmpl_id': self.product2.product_tmpl_id.id,
                'bom_line_ids': [
                    fields.Command.create({
                        'product_id': self.env.ref('product.product_product_6').id,
                        'product_qty': 2.0,
                        'bom_product_template_attribute_value_ids': [
                            fields.Command.link(variant1.id)
                        ]
                    })
                ]
            })


@tagged('common', 'manuf_variants')
class TestMrpProduction(TransactionCase):

    def setUp(self):
        super(TestMrpProduction, self).setUp()
        self.product_fp = self.env.ref('product.product_product_4_product_template')
        self.product_comp1 = self.env.ref('product.product_product_5')
        self.product_comp2 = self.env.ref('product.product_product_6')

        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_fp.id,
            'product_qty': 10,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'type': 'normal',
        })
        self.bom2 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_fp.id,
            'product_qty': 5,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'type': 'normal',
        })

        self.bom_line1 = self.env['mrp.bom.line'].create({
            'bom_id': self.bom.id,
            'product_id': self.product_comp1.id,
            'product_qty': 2,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.bom_line2 = self.env['mrp.bom.line'].create({
            'bom_id': self.bom.id,
            'product_id': self.product_comp2.id,
            'product_qty': 3,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.production = self.env['mrp.production'].create({
            'product_qty': 50,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'bom_id': self.bom.id,
            'state': 'draft',
        })

    def test_compute_move_raw_ids(self):
        """Test the computation of move raw IDs based on BoM components."""
        self.production._compute_move_raw_ids()

        raw_moves = self.production.move_raw_ids
        self.assertEqual(len(raw_moves), 2, "Expected two raw moves for the BoM components.")

        expected_values = [
            {
                'product_id': self.product_comp1.id,
                'product_qty': 10.0,
                'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            },
            {
                'product_id': self.product_comp2.id,
                'product_qty': 15.0,
                'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            },
        ]
        for move, expected in zip(raw_moves, expected_values):
            self.assertEqual(move.product_id.id, expected['product_id'], "Product ID mismatch.")
            self.assertAlmostEqual(move.product_qty, expected['product_qty'], msg="Product quantity mismatch.")
            self.assertEqual(move.product_uom.id, expected['product_uom_id'], "UoM mismatch.")

    def test_delete_move_raw_ids_on_no_bom(self):
        """Ensure move raw IDs are deleted when no BoM is assigned."""
        self.production.bom_id = False
        self.production._compute_move_raw_ids()
        self.assertFalse(self.production.move_raw_ids, "Move raw IDs should be deleted when no BoM is assigned.")

    def test_manual_move_entries_are_kept(self):
        """Ensure that manually entered move lines are retained."""
        manual_move = self.env['stock.move'].create({
            'name': 'Manual Move',
            'product_id': self.product_comp1.id,
            'product_uom_qty': 5,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'raw_material_production_id': self.production.id,
        })
        self.production._compute_move_raw_ids()
        self.assertIn(manual_move, self.production.move_raw_ids, "Manually entered move should be retained.")

    def test_no_bom_id(self):
        self.assertTrue(self.production.move_raw_ids)
        self.production.bom_id = False
        self.production._compute_move_raw_ids()
        self.assertFalse(self.production.move_raw_ids)

    def test_skip_compute_move_raw_ids_context(self):
        """Ensure the computation is skipped when the context contains 'skip_compute_move_raw_ids'."""
        self.production.move_raw_ids.unlink()
        with self.env.cr.savepoint():
            self.production.with_context(skip_compute_move_raw_ids=True)._compute_move_raw_ids()
            self.assertFalse(self.production.move_raw_ids, "Move raw IDs should not be computed due to context.")

    def test_clear_move_raw_ids_for_intermediate_bom(self):
        """Ensure move raw IDs are cleared if the BoM is intermediate and conditions are not met."""
        self.bom2.is_intermediate = True
        self.production.bom_id = self.bom2.id
        self.production._compute_move_raw_ids()
        self.assertFalse(self.production.move_raw_ids, "Move raw IDs should be cleared for intermediate BoM.")
