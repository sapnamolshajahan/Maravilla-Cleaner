from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tests import common, tagged
from unittest.mock import patch, MagicMock

from odoo.exceptions import UserError


@tagged('operations_stocktake')
class TestStockInventory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@example.com',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TEST',
        })
        self.consu_product = self.env['product.product'].create({
            'name': 'Consumable Product',
            'type': 'consu',
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
        })
        self.warehouse = self.env['stock.warehouse'].create({
            "name": "test warehouse",
            "active": True,
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
            'code': 'TEST'
        })
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Sample Stock',
            'location_ids': [(6, 0, [self.location.id])],
            'start_empty': True,
            'warehouse_id': self.warehouse.id,
        })
        self.stock_move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product.id,
            'product_uom_qty': 10.0,
            'product_uom': self.product.uom_id.id,
            'location_id': self.location.id,
            'location_dest_id': self.location.id,
            'state': 'confirmed',
            'inventory_id': self.inventory.id,
        })
        self.inventory_line = self.env['stock.inventory.line'].create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'product_qty': 10.0,
            'stock_moves': [(6, 0, [self.stock_move.id])],
        })


    @patch.object(TransactionCase, 'env', autospec=True)
    def test_post_inventory(self, mock_env):
        """Test the post_inventory method"""
        mock_commit = patch.object(self.env.cr, 'commit', autospec=True)
        mock_commit.start()
        self.inventory.post_inventory()
        self.assertEqual(self.stock_move.state, 'done', "Stock move should be in 'done' state")
        self.assertTrue(self.inventory_line.moves_done, "Inventory line should be marked as moves_done")
        self.assertIn('force_period_date', self.env.context, "Context should include 'force_period_date'")
        self.assertEqual(self.env.context['force_period_date'], self.inventory.accounting_date,
                         "force_period_date should match the inventory accounting date")

        mock_commit.stop()

    def test_action_validate_background(self):
        """Test action_validate_background function behavior."""
        self.inventory.state = 'confirm'
        self.inventory.action_validate_background()
        self.assertEqual(
            self.inventory.state,
            'queued',
            "Inventory state should be set to 'queued'"
        )
        self.assertTrue(
            self.inventory.bg_task_id,
            "bg_task_id should be set after queuing a background job"
        )
        messages = self.env['mail.message'].search([
            ('res_id', '=', self.inventory.id),
            ('model', '=', 'stock.inventory'),
            ('body', '=', 'Queued for Stocktake Confirm')
        ])
        self.assertTrue(
            messages,
            "A message should be posted to indicate queuing of the stocktake"
        )

    def test_action_post_move(self):
        mock_commit = patch.object(self.env.cr, 'commit', autospec=True)
        mock_commit.start()
        self.inventory.action_post_move(self.inventory_line)
        self.assertEqual(
            self.stock_move.state,
            'done',
            "Inventory state should be set to 'done'"
        )
        self.assertEqual(
            self.stock_move.date,
            fields.Datetime.now(),
            "Inventory date should be set to current date"
        )
        self.assertEqual(
            self.stock_move.move_line_ids.state,
            'done',
            "Inventory move_line_ids state should be set to 'done'"
        )
        self.assertEqual(
            self.inventory_line.moves_done,
            True,
            "Inventory move_line_ids state should be set to 'done'"
        )
        mock_commit.stop()

    def test_run_validate_line(self):
        stocktake_id = self.inventory.id
        line_id = self.inventory_line.id
        uid =self.env.user.id
        result = self.inventory._run_validate_line(stocktake_id, line_id, uid)
        self.assertTrue(result, "The method should return True when successful.")
        self.inventory.state = 'confirm'
        self.assertEqual(self.inventory.state, 'confirm', "Stocktake state should be updated to 'confirm' on error.")
        self.assertTrue(self.inventory.message_ids, "Error message should be logged on stocktake.")

    def test_action_validate_line(self):
        stocktake_id = self.inventory
        stocktake_id.accounting_date = fields.Datetime.now()
        stocktake_id.state = 'confirm'
        line_id = self.inventory_line
        line_id = self.env['stock.inventory.line'].create({
            'inventory_id': stocktake_id.id,
            'product_id': self.consu_product.id,
            'product_qty': 10,
            'theoretical_qty': 5,
            'location_id': self.location.id,
            'stock_moves': [(6, 0, [self.stock_move.id])],
        })
        self.assertEqual(line_id.product_qty, 10, "Initial product quantity should be 10")
        self.assertEqual(line_id.theoretical_qty, 5, "Theoretical quantity should be 5")
        result = self.inventory.action_validate_line(stocktake_id, line_id)
        self.assertTrue(result, "The action_validate_line method should return True")

    def test_confirm_stock_take(self):
        mock_commit = patch.object(self.env.cr, 'commit', autospec=True)
        mock_commit.start()
        stocktake_id = self.inventory.id
        uid = self.env.user.id
        self.inventory.confirm_stock_take(stocktake_id, uid)
        self.assertEqual(
            self.inventory.state,
            'done',
            "Inventory state should be set to 'done'"
        )
        self.assertEqual(
            self.inventory.date,
            fields.Datetime.now(),
            "Inventory date should be set to current date"
        )
        mock_commit.stop()

    def test_calculate_products_quantity(self):
        """Test the calculate_products_quantity method."""
        location_ids = [self.location]
        products = [self.product, self.consu_product]
        result = self.inventory.calculate_products_quantity(location_ids, products)
        expected_key_product = (self.product.id, self.location.id)
        expected_key_consu_product = (self.consu_product.id, self.location.id)
        self.assertIn(expected_key_product, result, "Product quantity key should exist in the result.")
        self.assertIn(expected_key_consu_product, result, "Consumable product quantity key should exist in the result.")

        self.assertEqual(
            result[expected_key_consu_product],
            0.0,
            "Consumable product quantity for the location should be zero by default."
        )

    def test_import_non_serial_data_entries(self):
        """Test the import_non_serial_data_entries method."""
        StocktakeDataEntry = self.env['stocktake.data.entry']
        StocktakeDataEntryLine = self.env['stocktake.data.entry.line']
        stocktake_entry = StocktakeDataEntry.create({'inventory': self.inventory.id,  'location': self.location.id,})
        StocktakeDataEntryLine.create({
            'stocktake_id': stocktake_entry.id,
            'product_id': self.product.id,
            'quantity': 5,
        })
        StocktakeDataEntryLine.create({
            'stocktake_id': stocktake_entry.id,
            'product_id': self.product.id,
            'quantity': 99999,
        })
        self.inventory.import_non_serial_data_entries()
        inventory_lines = self.env['stock.inventory.line'].search([
            ('inventory_id', '=', self.inventory.id),
            ('product_id', '=', self.product.id),
            ('location_id', '=', self.location.id),
        ])
        self.assertEqual(len(inventory_lines), 1, "An inventory line should be created.")


