from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged('operations_stocktake')
class TestInventoryLine(TransactionCase):

    def setUp(self):
        super(TestInventoryLine, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TEST',
        })
        self.product_name = self.env['product.product'].create({
            'name': 'Test Product sample',
            'type': 'consu',
            'default_code': 'TEST',
            'is_storable': False
        })
        self.company = self.env['res.company'].search([],limit=1)
        self.location = self.env['stock.location'].create({'name': 'Location 1', 'usage': 'internal'})
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Test Inventory',
            'company_id': self.company.id,
            'location_ids': [(6, 0, self.env['stock.location'].create([
                {'name': 'Test Location 1', 'company_id': self.company.id, 'usage': 'internal'},
                {'name': 'Test Location 2', 'company_id': self.company.id, 'usage': 'transit'},
            ]).ids)],
        })
        self.inventory_line = self.env['stock.inventory.line'].create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'company_id': self.company.id,
            'product_qty': 10.0,
            'theoretical_qty': 8.0,
        })
        self.location_src = self.env['stock.location'].create({
            'name': 'Source Location',
            'usage': 'internal',
        })
        self.location_dest = self.env['stock.location'].create({
            'name': 'Destination Location',
            'usage': 'internal',
        })
        self.picking_type = self.env['stock.picking.type'].create({
            'name': 'Internal Picking',
            'code': 'internal',
            'use_create_lots': False,
            'use_existing_lots': False,
            'default_location_src_id': self.location_src.id,
            'default_location_dest_id': self.location_dest.id,
            'sequence_code' :1
        })
        self.lot = self.env['stock.lot'].create({
            'name': 'Lot001',
            'product_id': self.product.id,
            'company_id': self.company.id,
        })

    def test_domain_location_id(self):
        """Test _domain_location_id when active model is stock.inventory"""
        self.env.context = {
            'active_model': 'stock.inventory',
            'active_id': self.inventory.id,
        }
        expected_domain = "[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit']), ('id', 'child_of', %s)]" % self.inventory.location_ids.ids
        computed_domain = self.inventory_line._domain_location_id()
        self.assertEqual(
            computed_domain,
            expected_domain,
            f"Expected domain {expected_domain}, but got {computed_domain}"
        )
        """Test _domain_location_id when no active inventory is set"""
        self.env.context = {}
        expected_domain ="[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]"
        computed_domain = self.inventory_line._domain_location_id()
        self.assertEqual(
            computed_domain,
            expected_domain,
            f"Expected domain {expected_domain}, but got {computed_domain}"
        )

    def test_domain_product_id(self):
        """Test _domain_product_id when active model is stock.inventory and inventory has multiple products"""
        product_1 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'consu',
            'default_code': 'P1',
        })
        product_2 = self.env['product.product'].create({
            'name': 'Product 2',
            'type': 'consu',
            'default_code': 'P2',
        })
        self.inventory.write({
            'product_ids': [(6, 0, [product_1.id, product_2.id])],
        })

        self.env.context = {
            'active_model': 'stock.inventory',
            'active_id': self.inventory.id,
        }
        expected_domain = "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', 'in', %s)]" % self.inventory.product_ids.ids
        computed_domain = self.inventory_line._domain_product_id()
        self.assertEqual(
            computed_domain,
            expected_domain,
            f"Expected domain {expected_domain}, but got {computed_domain}"
        )
        """Test _domain_product_id when active model is stock.inventory and inventory has one product"""

        product_1 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'consu',
            'default_code': 'P1',
        })
        self.inventory.write({
            'product_ids': [(6, 0, [product_1.id])],
        })

        self.env.context = {
            'active_model': 'stock.inventory',
            'active_id': self.inventory.id,
        }
        expected_domain = "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
        computed_domain = self.inventory_line._domain_product_id()
        self.assertEqual(
            computed_domain,
            expected_domain,
            f"Expected domain {expected_domain}, but got {computed_domain}"
        )

    def test_compute_difference_qty(self):
        """Test that the difference_qty is correctly computed"""
        self.inventory_line._compute_difference()
        self.assertEqual(
            self.inventory_line.difference_qty,
            2.0,
            f"Expected difference_qty to be 2.0, but got {self.inventory_line.difference_qty}"
        )
        self.inventory_line.write({
            'product_qty': 15.0,
            'theoretical_qty': 12.0,
        })
        self.inventory_line._compute_difference()
        self.assertEqual(
            self.inventory_line.difference_qty,
            3.0,
            f"Expected difference_qty to be 3.0, but got {self.inventory_line.difference_qty}"
        )
        self.inventory_line.write({
            'product_qty': 5.0,
            'theoretical_qty': 8.0,
        })
        self.inventory_line._compute_difference()
        self.assertEqual(
            self.inventory_line.difference_qty,
            -3.0,
            f"Expected difference_qty to be -3.0, but got {self.inventory_line.difference_qty}"
        )

    def test_create_theoretical_qty_set(self):
        """Test that theoretical_qty is set correctly during creation."""
        self.assertEqual(
            self.inventory_line.theoretical_qty,
            8.0,
            "Expected theoretical_qty to be set to the product's quantity in stock."
        )

        """Test that product_uom_id is set correctly during creation."""
        self.assertEqual(
            self.inventory_line.product_uom_id,
            self.product.uom_id,
            "Expected product_uom_id to be set to the product's default UoM."
        )

        """Test that theoretical_qty is not overwritten if provided."""

        self.assertEqual(
            self.inventory_line.theoretical_qty,
            8.0,
            "Expected theoretical_qty to remain unchanged if explicitly provided."
        )

    def test_move_dict_success(self):
        """Test the move_dict function generates the correct dictionary."""
        qty = 5.0
        move_dict = self.inventory_line.move_dict(qty, self.location_src.id, self.location_dest.id)
        self.assertEqual(move_dict['product_id'], self.product.id, "Product ID should match.")
        self.assertEqual(move_dict['product_uom_qty'], qty, "Product quantity should match the input.")
        self.assertEqual(move_dict['location_id'], self.location_src.id, "Source location should match.")
        self.assertEqual(move_dict['location_dest_id'], self.location_dest.id, "Destination location should match.")
        self.assertEqual(move_dict['picking_type_id'], self.picking_type.id, "Picking type should match.")
        self.assertEqual(move_dict['state'], 'confirmed', "State should be 'confirmed'.")
        self.assertEqual(move_dict['inventory_id'], self.inventory.id, "Inventory ID should match.")
        self.assertEqual(move_dict['reference'], f"INV:{self.inventory.name}",
                         "Reference should match the inventory name.")

        """Test that UserError is raised if no picking type is found."""
        self.picking_type.unlink()

        qty = 5.0
        with self.assertRaises(UserError) as e:
            self.inventory_line.move_dict(qty, self.location_src.id, self.location_dest.id)

        self.assertIn(
            "No valid operation type found. Set up operation type of internal and for Lot/Serial",
            str(e.exception),
            "Error message should match the validation."
        )

    def test_move_line_dict_success(self):
        """Test the move_line_dict function generates the correct dictionary."""
        qty = 5.0
        move_line_dict = self.inventory_line.move_line_dict(qty, self.location_src.id, self.location_dest.id, self.lot)
        self.assertEqual(move_line_dict['product_id'], self.product.id, "Product ID should match.")
        self.assertEqual(move_line_dict['quantity'], qty, "Quantity should match the input.")
        self.assertEqual(move_line_dict['location_id'], self.location_src.id, "Source location should match.")
        self.assertEqual(move_line_dict['location_dest_id'], self.location_dest.id,
                         "Destination location should match.")
        self.assertEqual(move_line_dict['product_uom_id'], self.product.uom_id.id, "Product UoM should match.")
        self.assertEqual(move_line_dict['company_id'], self.company.id, "Company ID should match.")
        self.assertEqual(move_line_dict['state'], 'confirmed', "State should be 'confirmed'.")
        self.assertEqual(move_line_dict['lot_id'], self.lot.id, "Lot ID should match.")
        self.assertEqual(move_line_dict['lot_name'], self.lot.name, "Lot name should match.")
        self.assertEqual(move_line_dict['reference'], f"INV:{self.inventory.name}",
                         "Reference should match the inventory name.")

        """Test move_line_dict with no lot provided."""
        qty = 5.0
        move_line_dict = self.inventory_line.move_line_dict(qty, self.location_src.id, self.location_dest.id, None)
        self.assertFalse(move_line_dict['lot_id'], "Lot ID should be False when no lot is provided.")
        self.assertFalse(move_line_dict['lot_name'], "Lot name should be False when no lot is provided.")


    def test_action_reset_product_qty(self):
        """Test the action_reset_product_qty function."""
        self.inventory_line.action_reset_product_qty()
        self.assertEqual(self.inventory_line.product_qty, 0.0,
                         "Product quantity should be reset to 0 for inventory lines.")
        self.inventory_line.state = 'in_progress'
        self.inventory_line.action_reset_product_qty()
        self.assertEqual( self.inventory_line.product_qty, 0.0,
                         "Product quantity should be reset to 0 for lines in progress.")

    def test_get_move_values(self):
        """Test move values generation."""
        qty = 2.0
        move_values = self.inventory_line._get_move_values(
            qty, self.location.id, self.location_src.id, None
        )
        self.assertEqual(move_values['product_id'], self.product.id, "Product ID mismatch in move values.")
