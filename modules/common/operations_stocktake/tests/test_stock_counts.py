from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged

from odoo import fields
from odoo.exceptions import UserError


@tagged('operations_stocktake')
class TestStockInventory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
        })
        self.warehouse = self.env["stock.warehouse"].create({
            "name": "Test Warehouse",
            "code": "TWH",
            "lot_stock_id": self.location.id,
            "view_location_id": self.env["stock.location"].create({
                "name": "Test Warehouse View Location",
                "usage": "view",
            }).id,
        })
        self.stock_inventory = self.env['stock.inventory'].create({
            'name': 'Test Inventory',
            'include_uncounted_items': True,
            'location_ids':self.location
        })


    def test_get_inventory_lines_values(self):
        quants = self.env['stock.quant'].create([{
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 10,
        }])

        values = self.stock_inventory._get_inventory_lines_values()
        self.assertTrue(values, "Inventory lines values should be returned.")
        self.assertEqual(len(values), len(quants), "Number of values should match number of quants.")


    def test_compute_bg_task_state(self):
        self.stock_inventory.bg_task_id = "test_uuid"
        self.env.cr.execute("INSERT INTO queue_job (uuid, state) VALUES (%s, %s)", ("test_uuid", "done"))
        self.stock_inventory._compute_bg_task_state()
        self.assertEqual(self.stock_inventory.bg_task_state, "Done")

    def test_action_create_child_queue(self):
        self.stock_inventory.line_ids = [(0, 0, {'product_id': self.product.id, 'location_id': self.location.id})]
        self.stock_inventory.action_create_child_queue(self.stock_inventory.id, self.env.user.id)
        self.assertTrue(self.stock_inventory.message_ids)

    def test_action_open_inventory_lines(self):
        action = self.stock_inventory.action_open_inventory_lines()
        self.assertEqual(action['res_model'], 'stock.inventory.line')
        self.assertIn('domain', action)

    def test_action_import_stock_counts(self):
        self.stock_inventory.stocktake_datas = [(0, 0, {'state': 'draft','location':self.location.id})]
        self.assertEqual(self.stock_inventory.stocktake_datas.state,"draft","state is seted to draft stage")
        result = self.stock_inventory.action_import_stock_counts()
        self.assertEqual(self.stock_inventory.stocktake_datas.state,"done","state is assigned to done stage")

