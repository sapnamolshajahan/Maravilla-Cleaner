from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import common, tagged
from odoo import fields
from unittest.mock import patch


@tagged('operations_stocktake')
class TestActionValidate(TransactionCase):

    def setUp(self):
        super().setUp()

        self.product_phantom = self.env['product.product'].create({
            'name': 'Phantom Product',
            'type': 'consu',
            'bom_ids': [(0, 0, {
                'type': 'phantom',
                'product_qty': 1.0,
                'bom_line_ids': []
            })]
        })

        self.product_consumable = self.env['product.product'].create({
            'name': 'Consumable Product',
            'type': 'consu',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TEST',
        })

        self.product_negative_qty = self.env['product.product'].create({
            'name': 'Negative Quantity Product',
            'type': 'consu',
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
        })
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Test Inventory Adjustment',
            'state': 'draft',
            'include_uncounted_items': True,
            'location_ids':  [(6, 0, [self.location.id])],
        })

        self.inventory.line_ids = [
            (0, 0, {
                'product_id': self.product_phantom.id,
                'product_qty': 5.0,
                'location_id': self.location.id
            }),
            (0, 0, {
                'product_id': self.product_consumable.id,
                'product_qty': 10.0,
                'location_id': self.location.id
            }),
            (0, 0, {
                'product_id': self.product_negative_qty.id,
                'product_qty': -2.0,
                'theoretical_qty': 0.0,
                'location_id': self.location.id
            })
        ]
        self.move_1 = self.env['stock.move'].create({
            'name': 'Test Move 1',
            'state': 'draft',
            'product_id': self.product.id,
            'product_uom_qty': 10.0,
            'location_id': self.location.id,
            'location_dest_id': self.location.id,
        })

        self.move_line_1 = self.env['stock.move.line'].create({
            'move_id': self.move_1.id,
            'product_id': self.move_1.product_id.id,
            'product_uom_id': self.move_1.product_uom.id,
            'qty_done': 0,
            'location_id': self.move_1.location_id.id,
            'location_dest_id': self.move_1.location_dest_id.id,
        })
        self.location_1 = self.env['stock.location'].create({
            'name': 'Test Location 1',
            'usage': 'internal',
        })
        self.location_2 = self.env['stock.location'].create({
            'name': 'Test Location 2',
            'usage': 'internal',
        })
        self.warehouse = self.env['stock.warehouse'].create({'name': 'Warehouse 1', 'code': 'WH1'})


    def test_action_validate(self):
        """Test the action_validate method."""
        self.inventory.state = 'confirm'
        self.inventory.accounting_date = fields.Datetime.now()
        with self.assertRaises(UserError):
            self.inventory.action_validate()

        negative_line = self.inventory.line_ids.filtered(
            lambda l: l.product_id == self.product_negative_qty
        )
        negative_line.product_qty = 0.0

        self.inventory.action_validate()
        self.assertEqual(self.inventory.state, 'done', "Inventory state should be 'done'")
        consumable_line = self.inventory.line_ids.filtered(
            lambda l: l.product_id == self.product_consumable
        )
        self.assertFalse(consumable_line, "Consumable product line should be unlinked.")

    def test_compute_unprocessed_moves(self):
        """Test the _compute_unprocessed_moves function."""
        self.move_line_1.write({'state': 'done'})
        self.inventory._compute_unprocessed_moves()
        self.assertFalse(self.inventory.has_unprocessed_move_lines,
                         "The record should not have unprocessed move lines after marking moves as done.")
        self.move_line_1.write({'state': 'cancel'})
        self.inventory._compute_unprocessed_moves()
        self.assertFalse(self.inventory.has_unprocessed_move_lines,
                         "The record should not have unprocessed move lines after cancelling moves.")

    def test_action_validate_unprocessed_lines(self):
        """Test the action_validate_unprocessed_lines method."""
        unprocessed_move = self.env['stock.move'].create({
            'name': 'Unprocessed Move',
            'state': 'assigned',
            'product_id': self.product.id,
            'product_uom_qty': 5.0,
            'location_id': self.location.id,
            'location_dest_id': self.location.id,
        })
        self.inventory.move_ids = [(4, unprocessed_move.id)]
        self.assertEqual(unprocessed_move.state, 'assigned', "Initial stock move state should be 'assigned'.")
        self.inventory.action_validate_unprocessed_lines()
        self.assertEqual(unprocessed_move.state, 'done', "Stock move state should be 'done' after validation.")
        self.assertTrue(
            all(line.state == 'done' for line in unprocessed_move.move_line_ids),
            "All move lines should be in the 'done' state after validation."
        )
        self.assertEqual(self.inventory.state, 'done', "Inventory state should be 'done' after validation.")


    def test_action_view_related_count_lines(self):
        """Test the action_view_related_count_lines method."""
        inventory_line_1 = self.env['stock.inventory.line'].create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'product_qty': 10.0,
            'location_id': self.location.id,
        })
        action = self.inventory.action_view_related_count_lines()
        self.assertEqual(action['name'], 'Counts', "The action name should be 'Counts'.")
        self.assertEqual(action['type'], 'ir.actions.act_window', "The action type should be 'ir.actions.act_window'.")
        self.assertEqual(action['res_model'], 'stock.inventory.line',
                         "The action model should be 'stock.inventory.line'.")
        self.assertEqual(action['view_type'], 'list', "The view_type should be 'list'.")
        self.assertEqual(action['view_mode'], 'list', "The view_mode should be 'list'.")
        expected_domain = [('inventory_id', '=', self.inventory.id)]
        self.assertEqual(action['domain'], expected_domain, "The domain should filter by the current inventory ID.")
        inventory_lines = self.env['stock.inventory.line'].search([('inventory_id', '=', self.inventory.id)])
        self.assertIn(inventory_line_1.id, inventory_lines.ids,
                      "Inventory line 1 should be associated with the inventory.")

    def test_action_cancel_draft(self):
        """Test the action_cancel_draft method."""
        self.inventory.write({'state': 'confirm', 'allow_cancel': True})
        move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product.id,
            'product_uom_qty': 10.0,
            'location_id': self.location.id,
            'location_dest_id': self.location.id,
            'state': 'assigned',
            'inventory_id': self.inventory.id,
        })
        self.inventory.action_cancel_draft()
        self.assertEqual(self.inventory.state, 'draft', "Inventory state should be 'draft' after cancellation.")
        self.assertFalse(self.inventory.line_ids, "Inventory lines should be unlinked after cancellation.")
        self.assertEqual(move.state, 'cancel', "Related stock moves should be canceled.")

    def test_action_start(self):
        """Test the action_start method."""
        stock_valuation_account = self.env['account.account'].create({'name': 'Stock Valuation', 'code': 'SV01', })
        stock_input_account = self.env['account.account'].create({'name': 'Stock Input', 'code': 'SI01',  })
        stock_output_account = self.env['account.account'].create({'name': 'Stock Output', 'code': 'SO01',  })
        category_1 = self.env['product.category'].create({
            'name': 'Category 1',
            'property_stock_valuation_account_id': stock_valuation_account.id,
            'property_stock_account_input_categ_id': stock_input_account.id,
            'property_stock_account_output_categ_id': stock_output_account.id,
        })
        product_in_category = self.env['product.product'].create({
            'name': 'Product in Category',
            'categ_id': category_1.id,
        })
        self.inventory.write({'category_ids': [(4, category_1.id)], 'prepopulate_lines': True})
        action = self.inventory.action_start()
        self.assertEqual(self.inventory.state, 'confirm', "Inventory state should be 'confirm' after starting.")
        self.assertIn(product_in_category.id, self.inventory.product_ids.ids,
                      "Products from selected categories should be added to the inventory.")


    def test_action_start_creates_lines(self):
        """Test that _action_start creates inventory lines."""
        self.assertEqual(self.inventory.state, 'draft', "Initial state should be 'draft'.")
        self.inventory._action_start()
        self.assertEqual(self.inventory.state, 'confirm', "State should change to 'confirm' after starting.")
        """Test that _action_start does not create lines when start_empty is True."""
        self.inventory.start_empty = True
        self.inventory._action_start()
        self.assertEqual(self.inventory.state, 'confirm', "State should change to 'confirm' even with start_empty.")
        """Test that _action_start skips inventories not in draft state."""
        self.inventory.state = 'confirm'
        self.inventory._action_start()
        self.assertEqual(self.inventory.state, 'confirm', "State should remain 'confirm'.")
        """Test that _action_start uses inventory lines when product and location are set."""
        self.inventory.write({
            'product_ids': [(4, self.product.id)],
            'location_ids': [(4, self.location.id)],
        })
        self.inventory._action_start()
        self.assertEqual(self.inventory.state, 'confirm', "State should change to 'confirm'.")
        self.assertTrue(self.inventory.line_ids, "Inventory lines should be created.")


    def test_action_view_related_move_lines(self):
        """Test that the action returns the correct domain and model."""
        action = self.inventory.action_view_related_move_lines()
        self.assertIsInstance(action, dict, "The action should return a dictionary.")
        self.assertEqual(action.get('res_model'), 'stock.move.line', "The model should be 'stock.move.line'.")
        self.assertIn('domain', action, "The action should include a domain.")
        expected_domain = [('move_id', 'in', self.inventory.move_ids.ids)]
        self.assertEqual(action['domain'], expected_domain, "The domain should filter by move_ids.")
        self.assertEqual(action.get('view_mode'), 'list,form', "The view mode should be 'list,form'.")
        self.assertEqual(action.get('type'), 'ir.actions.act_window',
                         "The action type should be 'ir.actions.act_window'.")

    def test_add_include_uncounted_items(self):
        """Test the `add_include_uncounted_items` method."""
        mock_commit = patch.object(self.env.cr, 'commit', autospec=True)
        mock_commit.start()
        uncounted_product = self.env['product.product'].create({
            'name': 'Uncounted Product',
            'type': 'consu',
        })
        self.env['stock.move'].create({
            'name': 'Uncounted Product Move',
            'product_id': uncounted_product.id,
            'product_uom_qty': 5.0,
            'product_uom': uncounted_product.uom_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.location.id,
            'state': 'done',
        })
        self.inventory.add_include_uncounted_items()
        self.assertEqual(len(self.inventory.line_ids), 3, "Inventory lines should now contain three lines.")
        mock_commit.stop()

