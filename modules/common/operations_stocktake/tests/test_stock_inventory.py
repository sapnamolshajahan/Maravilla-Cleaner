from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged

@tagged('operations_stocktake')
class TestInventory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.customer_location = self.env['stock.location'].create({
            'name': 'Customer Location',
            'usage': 'customer',
        })
        self.view_location = self.env['stock.location'].create({
            'name': 'Warehouse View Location',
            'usage': 'internal',
        })
        self.warehouse = self.env['stock.warehouse'].create({
            "name": "test warehouse",
            "active": True,
            'reception_steps': 'one_step',
            'delivery_steps': 'ship_only',
            'code': 'TEST'
        })
        self.warehouse.view_location_id = self.view_location
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Sample Stock',
            'location_ids': [(6, 0, [self.customer_location.id])],
            'start_empty': True,
            'warehouse_id': self.warehouse.id,
        })

        self.product_model = self.env['product.product']
        self.template_model = self.env['product.template']
        self.location_model = self.env['stock.location']
        self.view_location = self.env['stock.location'].search([('usage', '=', 'view')], limit=1)
        self.company = self.env['res.company'].search([], limit=1)
        self.product_template_1 = self.template_model.create({
            'name': 'Product Template',
            'type': "consu",
            'company_id': self.company.id,
        })
        self.product_1 = self.product_model.create({
            'product_tmpl_id': self.product_template_1.id,
            'list_price': 100.0,
            'is_storable': True,
        })
        self.product_11 = self.env['product.product'].create({
            'name': 'Test Product 1',
            'type': 'consu',
        })
        self.product_22 = self.env['product.product'].create({
            'name': 'Test Product 2',
            'type': 'consu',
        })
        self.env['stock.move'].create({
            'name': 'Move 1',
            'product_id': self.product_11.id,
            'product_uom_qty': 10,
            'location_id': self.customer_location.id,
            'location_dest_id': self.customer_location.id,
            'state': 'done',
        })
        self.env['stock.move'].create({
            'name': 'Move 2',
            'product_id': self.product_22.id,
            'product_uom_qty': 5,
            'location_id': self.customer_location.id,
            'location_dest_id': self.customer_location.id,
            'state': 'done',
        })

    def test_compute_location_ids_domain(self):
        inventory = self.inventory
        inventory.warehouse_id = False
        inventory._compute_location_ids_domain()
        expected_domain = [('usage', 'in', ['internal', 'transit'])]
        self.assertEqual(inventory.location_ids_domain, expected_domain,
                         "Domain should only include internal and transit locations.")
        inventory.warehouse_id = self.warehouse
        inventory._compute_location_ids_domain()
        warehouse_location_ids = self.env['stock.location'].search(
            [('location_id', '=', self.warehouse.view_location_id.id)]).ids
        expected_domain_with_warehouse = ['&',('usage', 'in', ['internal', 'transit']),
                                          ('id', 'in', warehouse_location_ids)]
        self.assertEqual(inventory.location_ids_domain, expected_domain_with_warehouse,
                         "Domain should include locations related to the warehouse view location.")

    def test_onchange_warehouse(self):
        self.inventory.warehouse_id = False
        result = self.inventory._onchange_warehouse()
        expected_domain = [('usage', 'in', ['internal', 'transit'])]
        self.assertEqual(
            result['domain']['location_ids'],
            expected_domain,
            "Domain should only include internal and transit locations when no warehouse is selected."
        )
        warehouse_view_location = self.warehouse.view_location_id
        transit_location_1 = self.env['stock.location'].create({
            'name': 'Transit Location 1',
            'usage': 'transit',
            'location_id': warehouse_view_location.id,
        })
        self.inventory.warehouse_id = self.warehouse
        result = self.inventory._onchange_warehouse()
        warehouse_location_ids = self.env['stock.location'].search(
            [('location_id', '=', self.warehouse.view_location_id.id)]
        ).ids
        self.assertIn(transit_location_1.id, warehouse_location_ids,
                      "Transit location should be linked to the warehouse view location.")
        self.assertEqual(
            result['domain']['location_ids'],
            [('id', 'in', warehouse_location_ids)],
            "Domain should include locations related to the warehouse view location."
        )


    def test_copy_data(self):
        """
        Test that the copy_data method appends '(copy)' to the name.
        """
        copied_data = self.inventory.copy_data()[0]  # copy_data() returns a list of dictionaries
        self.assertIn(
            "(copy)", copied_data['name'],
            "The copied data's name does not include '(copy)'."
        )


    def test_calculate_products_quantity(self):
        """
        Test the calculate_products_quantity method for multiple products and locations.
        """
        location_ids = [self.view_location]
        products = [self.product_1]
        result = self.inventory.calculate_products_quantity(location_ids, products)
        expected_result = {
            (self.product_1.id, self.view_location.id): 0.0,
        }
        self.assertEqual(
            result, expected_result,
            "The calculated product quantities do not match the expected results."
        )


    def test_get_selection_name(self):
        """Test the `get_selection_name` function."""
        result = self.inventory.get_selection_name(
            self.env['queue.job'],
            'state',
            'done'
        )
        self.assertEqual(result, 'Done', "The selection name should match the expected value.")

    def test_allow_cancel(self):
        """Test the `_allow_cancel` function."""
        self.inventory._allow_cancel()
        self.assertTrue(self.inventory.allow_cancel, "Allow cancel should be True when no moves are done.")
        move_done = self.env['stock.move'].create({
            'name': 'Done Move',
            'state': 'done',
            'inventory_id': self.inventory.id,
            'product_id':self.product_1.id,
            'location_id':self.customer_location.id,
            'location_dest_id':self.customer_location.id,

        })
        self.inventory.move_ids += move_done
        self.inventory._allow_cancel()
        self.assertFalse(self.inventory.allow_cancel, "Allow cancel should be False when a move is done.")



