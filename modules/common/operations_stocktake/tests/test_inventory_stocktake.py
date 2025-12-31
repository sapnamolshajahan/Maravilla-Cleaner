from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged('operations_stocktake')
class TestActionValidate(TransactionCase):

    def setUp(self):
        super().setUp()

        self.company = self.env.company
        self.product_1 = self.env['product.product'].create({'name': 'Product 1', 'type': 'consu'})
        self.product_2 = self.env['product.product'].create({'name': 'Product 2', 'type': 'consu'})
        self.location_1 = self.env['stock.location'].create({'name': 'Location 1', 'usage': 'internal'})
        self.location_2 = self.env['stock.location'].create({'name': 'Location 2', 'usage': 'internal'})
        self.warehouse = self.env['stock.warehouse'].create({'name': 'Warehouse 1', 'code': 'WH1'})
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Test Inventory',
            'state': 'draft',
            'company_id': self.company.id,
            'product_ids': [(6, 0, [self.product_1.id])],
            'location_ids': [(6, 0, [self.location_1.id])],
        })
        self.lot = self.env["stock.lot"].create({
            "name": "Test Lot",
            "product_id": self.product_1.id,
        })
        self.stocktake = self.env["stocktake.data.entry"].create({
            "inventory": self.inventory.id,
            "location": self.env["stock.location"].create({"name": "Test Location"}).id,
        })
        self.data_entry_line = self.env["stocktake.data.entry.line"].create({
            "stocktake_id": self.stocktake.id,
            "product_id": self.product_1.id,
            "production_lot_id": self.lot.id,
            "quantity": 1.0,
        })


    def test_get_exhausted_inventory_lines_vals(self):
        """Test _get_exhausted_inventory_lines_vals with specific products and locations."""
        non_exhausted_set = {(self.product_1.id, self.location_1.id)}
        vals = self.inventory._get_exhausted_inventory_lines_vals(non_exhausted_set)
        self.assertEqual(len(vals), 0, "No exhausted lines should be returned as all products are in the non-exhausted set.")
        non_exhausted_set = {(self.product_1.id, self.location_1.id)}
        self.inventory.location_ids = [(6, 0, [self.location_1.id, self.location_2.id])]
        vals = self.inventory._get_exhausted_inventory_lines_vals(non_exhausted_set)
        expected_vals = [{'product_id': self.product_1.id, 'location_id': self.location_2.id, 'theoretical_qty': 0}]
        self.assertEqual(len(vals), 1, "Only one line should be generated for the exhausted product-location pair.")
        self.assertEqual(vals[0]['location_id'], expected_vals[0]['location_id'])

    def test_enumerate_production_lots(self):
        """Test that enumerate_production_lots correctly finds lots and raises errors if missing."""
        product = self.env["product.product"].create({"name": "Test Product"})
        base_production = self.env["stock.lot"].create({
            "name": "LOT001",
            "product_id": product.id,
        })
        self.env["stock.lot"].create({"name": "LOT002", "product_id": product.id})
        self.env["stock.lot"].create({"name": "LOT003", "product_id": product.id})
        lots = self.inventory.enumerate_production_lots(base_production, 3)
        self.assertEqual(len(lots), 3, "Expected 3 lots in the result")
        self.assertEqual(lots[0].name, "LOT001", "First lot should match base production")
        self.assertEqual(lots[1].name, "LOT002", "Second lot should be LOT002")
        self.assertEqual(lots[2].name, "LOT003", "Third lot should be LOT003")
        with self.assertRaises(UserError):
            self.inventory.enumerate_production_lots(base_production, 5)


    def test_import_serial_data_entries_success(self):
        """Test successful import of serial data entries."""
        self.inventory.import_serial_data_entries()
        inventory_lines = self.env["stock.inventory.line"].search([("inventory_id", "=", self.inventory.id)])
        self.assertEqual(len(inventory_lines), 1, "One inventory line should be created.")
        self.assertEqual(inventory_lines.product_id, self.product_1, "The product should match the data entry line.")
        self.assertEqual(inventory_lines.prod_lot_id, self.lot, "The production lot should match the data entry line.")


