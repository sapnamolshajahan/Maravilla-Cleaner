from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged


@tagged('operations_stocktake')
class TestStockTakeDataEntry(TransactionCase):
    def setUp(self):
        super().setUp()
        self.stock_location = self.env["stock.location"].create({
            "name": "Test Stock Location",
            "usage": "internal",
        })
        self.warehouse = self.env["stock.warehouse"].create({
            "name": "Test Warehouse",
            "code": "TWH",
            "lot_stock_id": self.stock_location.id,
            "view_location_id": self.env["stock.location"].create({
                "name": "Test Warehouse View Location",
                "usage": "view",
            }).id,
        })
        self.inventory = self.env["stock.inventory"].create({
            "name": "Test Inventory",
            "warehouse_id": self.warehouse.id,
            "location_ids": [(6, 0, [self.stock_location.id])],
        })
        self.data_entry = self.env["stocktake.data.entry"].create({
            "inventory": self.inventory.id,
            "location": self.stock_location.id,
        })

    def test_inventory_locations(self):
        """Test the `_inventory_locations` compute method."""
        self.data_entry._inventory_locations()
        self.assertEqual(
            self.data_entry.inventory_locations,
            self.warehouse.lot_stock_id,
            "The inventory location should match the warehouse stock location."
        )

    def test_onchange_inventory(self):
        """Test the `onchange_inventory` method."""
        self.data_entry.inventory = self.inventory
        self.data_entry.onchange_inventory()
        self.assertEqual(
            self.data_entry.name,
            self.inventory.name,
            "The name should be updated to match the inventory name."
        )

    def test_get_display_name(self):
        """Test the `_get_display_name` compute method."""
        self.data_entry.location = self.warehouse.lot_stock_id
        self.data_entry.counter = 1
        self.data_entry._get_display_name()
        expected_display_name = "{}/{}/{}".format(
            self.inventory.name,
            self.warehouse.lot_stock_id.display_name,
            self.data_entry.counter
        )
        self.assertEqual(
            self.data_entry.display_name,
            expected_display_name,
            "The display name should be formatted correctly."
        )

    def test_create(self):
        """Test the create method of StockTakeDataEntry."""
        new_inventory = self.env["stock.inventory"].create({
            "name": "Another Test Inventory",
            "warehouse_id": self.warehouse.id,
            "location_ids": [(6, 0, [self.stock_location.id])],
            "state": "draft",
        })

        data_entry = self.env["stocktake.data.entry"].create({
            "inventory": new_inventory.id,
            "location": self.stock_location.id,
        })
        self.assertTrue(data_entry, "StockTakeDataEntry record should be created successfully")
        self.assertEqual(data_entry.inventory.id, new_inventory.id, "Inventory ID should match the created record")

    def test_action_reset(self):
        """Test the action_reset method of StockTakeDataEntry."""
        self.data_entry.write({"state": "done"})
        self.data_entry.action_reset()
        self.assertEqual(self.data_entry.state, "draft", "State should be reset to 'draft'")

    def test_unlink(self):
        """Test the unlink method of StockTakeDataEntry."""
        self.data_entry.write({"state": "draft"})
        self.data_entry.unlink()
        remaining_records = self.env["stocktake.data.entry"].search([("id", "=", self.data_entry.id)])
        self.assertFalse(remaining_records, "Record should be deleted successfully")
