# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("common", "manuf_outwork")
class TestMRPWorkorder(TransactionCase):

    def setUp(self):
        super(TestMRPWorkorder, self).setUp()
        self.partner_supplier = self.env['res.partner'].create({
            'name': 'Supplier 1',
            'is_company': True,
            'supplier_rank': 1,
        })
        self.service_product = self.env['product.product'].create({
            'name': 'Outwork Service',
            'type': 'service',
        })
        self.workcenter = self.env['mrp.workcenter'].create({
            'name': 'Outwork Center',
            'type': 'outwork',
            'partner': self.partner_supplier.id,
            'product': self.service_product.id,
        })
        self.production = self.env['mrp.production'].create({
            'name': 'Test Production',
            'product_id': self.ref('mrp.product_product_computer_desk'),
            'product_qty': 11,
            'bom_id': self.ref("mrp.mrp_bom_desk"),
            'product_uom_id': self.ref('uom.product_uom_unit')
        })

    def test_create_workorder_outwork(self):
        """Test the automatic creation of a Purchase Order when an outwork type Workorder is created."""
        workorder_vals = {
            'name': 'TEST Workorder',
            'workcenter_id': self.workcenter.id,
            'production_id': self.production.id,
            'product_uom_id': self.ref('uom.product_uom_unit')
        }
        existing_po = self.env['purchase.order'].search([('partner_id', '=', self.workcenter.partner.id),
                                                         ('state', '=', 'draft')])
        self.assertFalse(existing_po)
        workorder = self.env['mrp.workorder'].create(workorder_vals)
        self.assertEqual(workorder.type, 'outwork')
        self.assertEqual(workorder.partner.id, self.partner_supplier.id)
        self.assertEqual(workorder.product.id, self.service_product.id)
        purchase_order = workorder.purchase_order
        self.assertTrue(purchase_order, "A purchase order should have been created.")
        self.assertEqual(purchase_order.partner_id.id, self.partner_supplier.id)
        po_line = self.env['purchase.order.line'].search([('order_id', '=', purchase_order.id)])
        self.assertEqual(po_line.product_id.id, self.service_product.id)
        self.assertEqual(po_line.product_qty, 11, "The product quantity should match the production quantity.")

    def test_create_workorder_outwork_existing_po(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.workcenter.partner.id,
            'state': 'draft'})
        self.env.company.aggregate_po = True
        workorder_vals = {
            'name': 'TEST Workorder',
            'workcenter_id': self.workcenter.id,
            'production_id': self.production.id,
            'product_uom_id': self.ref('uom.product_uom_unit')
        }
        existing_po = self.env['purchase.order'].search([('partner_id', '=', self.workcenter.partner.id),
                                                         ('state', '=', 'draft')])
        self.assertTrue(existing_po)
        workorder = self.env['mrp.workorder'].create(workorder_vals)
        workorder_purchase_order = workorder.purchase_order
        self.assertTrue(workorder_purchase_order, "A purchase order should have been created.")
        self.assertEqual(workorder_purchase_order, purchase_order, "A purchase order should have been created.")
