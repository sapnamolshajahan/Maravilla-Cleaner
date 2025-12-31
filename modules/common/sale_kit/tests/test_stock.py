# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestPhantomKits(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.location_stock = cls.env.ref('stock.stock_location_stock')
        cls.location_customer = cls.env.ref('stock.stock_location_customers')
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

        cls.component = cls.env['product.product'].create({
            'name': 'Component A',
            'type': 'consu',
            'is_storable': True,
            'standard_price': 20.0,
        })

        cls.kit = cls.env['product.product'].create({
            'name': 'Kit Product',
            'type': 'consu',
            'is_storable': True,
            'standard_price': 100.0,
        })

        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.kit.product_tmpl_id.id,
            'type': 'phantom',
            'bom_line_ids': [(0, 0, {
                'product_id': cls.component.id,
                'product_qty': 2.0,
                'product_uom_id': cls.uom_unit.id,
            })]
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

        cls.sale_order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.kit.id,
            'product_uom_qty': 3.0,
            'price_unit': 150.0,
            'product_uom': cls.uom_unit.id,
        })

        # Simulate incoming stock for component
        cls.env['stock.quant']._update_available_quantity(cls.component, cls.location_stock, 5.0)

        # Confirm sale to create pickings
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids[0]
        cls.move = cls.picking.move_ids.filtered(lambda m: m.product_id == cls.component)


    def test_action_done_with_partial_kit(self):
        """Test that delivery with partial kits raises error"""
        self.move._ensure_for_full_kits()
        self.picking.action_assign()
        with self.assertRaises(UserError) as e:
            self.picking._action_done()
            self.assertIn("Not enough components to dispatch full kits", str(e.exception))

    def test_return_invoice_line_for_kit_component(self):
        """Test that returns for kit components get 0 price invoice lines"""
        # Set up return move manually
        picking = self.picking
        component_move = picking.move_ids.filtered(lambda m: m.product_id == self.component)
        return_move = component_move.copy({
            'origin_returned_move_id': component_move.id,
            'location_id': self.location_customer.id,
            'location_dest_id': self.location_stock.id,
        })
        values = picking._prepare_invoice_line_sale_return(return_move, self.partner)
        self.assertEqual(values['price_unit'], 0.0)
        self.assertIn('Return of kit component', values['name'])
