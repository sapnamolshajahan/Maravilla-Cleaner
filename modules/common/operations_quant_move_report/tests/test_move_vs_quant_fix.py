# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('common', 'operations_quant_move_report')
class TestOperationsMovesQuantsFix(TransactionCase):

    def setUp(self):
        super(TestOperationsMovesQuantsFix, self).setUp()
        self.fix_model = self.env["operations.moves.quants.fix"].create({})

        self.product = self.env["product.product"].create(
            {"name": "Test Product", "type": "consu", 'is_storable': True})
        self.location = self.env["stock.location"].create({"name": "Test Location", "usage": "internal"})
        self.lot = self.env["stock.lot"].create({"name": "Test Lot", "product_id": self.product.id})
        self.package = self.env["stock.quant.package"].create({"name": "Test Package"})
        self.product_package = self.env["product.packaging"].create(
            {"name": "Test Product Package", "product_id": self.product.id})
        self.stock_move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product.id,
            'product_uom_qty': 10.0,
            'location_id': self.location.id,
            'location_dest_id': self.location.id,
            'picking_id': self.env['stock.picking'].create({
                'name': 'Test Picking',
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
            }).id,
        })

    def create_stock_move_line(self, product, location, lot, package, qty, state='done'):
        move_line = self.env["stock.move.line"].create({
            "product_id": product.id,
            "location_id": location.id,
            "location_dest_id": location.id,
            "lot_id": lot.id if lot else False,
            "package_id": package.id if package else False,
            "quantity": qty,
            "company_id": self.env.company.id,
            "move_id": self.stock_move.id
        })
        move_line.state = state
        return move_line

    def create_stock_quant(self, product, location, lot, package, qty, reserved_qty=0):
        return self.env["stock.quant"].create({
            "product_id": product.id,
            "location_id": location.id,
            "lot_id": lot.id if lot else False,
            "package_id": package.id if package else False,
            "quantity": qty,
            "reserved_quantity": reserved_qty,
        })

    def test_get_stock_moves_soh_same_location(self):
        self.create_stock_move_line(self.product, self.location, self.lot, self.package, 10)
        soh = self.fix_model.get_stock_moves_soh(self.product.id, self.location, self.lot.id, self.package.id)
        self.assertEqual(soh, 0.0, "Stock on Hand calculation is incorrect")

    def test_get_stock_moves_soh_different_location(self):
        self.create_stock_move_line(self.product, self.env.ref('stock.stock_location_stock'), self.lot, self.package,
                                    10).location_dest_id = self.location.id
        soh = self.fix_model.get_stock_moves_soh(self.product.id, self.location, self.lot.id, self.package.id)
        self.assertEqual(soh, 10, "Stock on Hand calculation is incorrect")

    def test_get_stock_moves_soh_outgoing(self):
        """Test when stock moves out of the location."""
        move_line = self.create_stock_move_line(self.product, self.location, self.lot, self.package, 10)
        move_line.write({'location_dest_id': self.env.ref('stock.stock_location_customers').id})
        soh = self.fix_model.get_stock_moves_soh(self.product.id, self.location, self.lot.id, self.package.id)
        self.assertEqual(soh, -10, "Stock on Hand should decrease when moving out of location")

    def test_get_stock_moves_soh_incoming(self):
        """Test when stock moves into the location."""
        move_line = self.create_stock_move_line(self.product, self.env.ref('stock.stock_location_suppliers'), self.lot,
                                                self.package, 15)
        move_line.write({'location_dest_id': self.location.id})
        soh = self.fix_model.get_stock_moves_soh(self.product.id, self.location, self.lot.id, self.package.id)
        self.assertEqual(soh, 15, "Stock on Hand should increase when moving into location")

    def test_get_stock_moves_soh_no_lot_no_package(self):
        """Test when there is no lot and no package specified."""
        move_line = self.create_stock_move_line(self.product, self.location, None, None, 20)
        move_line.write({
            'location_dest_id': self.env.ref('stock.stock_location_stock').id
        })
        soh = self.fix_model.get_stock_moves_soh(self.product.id, self.location, None, None)
        self.assertEqual(soh, -20, "Stock calculation should handle missing lot/package")

    def test_get_stock_moves_soh_no_matching_moves(self):
        """Test when no stock moves match the criteria."""
        soh = self.fix_model.get_stock_moves_soh(self.product.id, self.location, self.lot.id, self.package.id)
        self.assertEqual(soh, 0.0, "Stock on Hand should be zero when no matching stock moves exist")

    def test_get_stock_moves_reserved(self):
        test_move_line = self.create_stock_move_line(self.product, self.location, self.lot, self.package, 5,
                                                     state='assigned')
        test_move_line.write({
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'product_packaging_qty': 5
        })
        reserved = self.fix_model.get_stock_moves_reserved(self.product.id, self.location, self.lot.id, self.package.id)
        self.assertEqual(reserved, 5, "Reserved stock calculation is incorrect")
