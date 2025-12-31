from odoo.tests import common, tagged

@tagged('operations_stock_adjustment')
class TestAccountMoveCurrent(common.TransactionCase):
    """Tests for inventory and account move adjustments."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': 'True',
            'list_price': 100.0,
            'sale_line_warn': 'no-message',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.operations_adjustment_reason = self.env['operations.adjustment.reason'].create({
            'name': 'Test Reason',
        })
        self.customer_location = self.env['stock.location'].create({
            'name': 'Customer Location',
            'usage': 'customer',
        })
        self.stock_move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom': self.product.uom_id.id,
            'location_id':  self.customer_location.id,
            'location_dest_id': self.customer_location.id,
            'operations_adjustment_reason': self.operations_adjustment_reason.id,
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })
        self.stock_quant = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 50.0,
        })
        self.inventory_adjustment = self.env['stock.inventory.adjustment.name'].create({
            'quant_ids': self.stock_quant,
        })
        self.approver_user = self.env['res.users'].create({
            'name': 'Test Approver',
            'login': 'approver',
        })
        self.user_non_approver = self.env['res.users'].create({
            'name': 'Test Non-Approver',
            'login': 'non_approver',
        })
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'password': 'test_password',
        })


    def test_action_apply_button_visibility(self):
        """Test the visibility of the apply button based on user roles."""
        self.env.company.adjustment_approver = self.approver_user
        context = dict(self.env.context, active_domain=[['location_id.usage', 'in', ['internal', 'transit']]])
        action_apply = self.env['stock.quant'].with_user(self.approver_user).with_context(context).action_apply_all()
        wizard_context = action_apply.get('context', {})
        action = action_apply
        wizard_action1 = (self.env['stock.inventory.adjustment.name']
                  .with_user(self.approver_user)
                  .with_context(wizard_context).create({}))
        wizard_action2 = (self.env['stock.inventory.adjustment.name']
                  .with_user(self.user_non_approver)
                  .with_context(wizard_context).create({}))

        self.assertEqual(wizard_action1.state, 'waiting', "Wizard for approver user is not in the expected 'waiting' state.")
        self.assertEqual(wizard_action2.state, 'done', "Wizard for non-approver user is not in the expected 'done' state.")

    def test_onchange_inventory_quantity(self):
        """Test onchange behavior when updating inventory quantity."""
        self.env.user = self.test_user
        self.assertFalse(self.stock_quant.user_id, "Initially, user_id should be unset.")
        self.stock_quant.inventory_quantity = 60
        self.stock_quant._onchange_inventory_quantity()
        self.assertEqual(self.stock_quant.user_id.id, self.test_user.id,
                         "The user_id should be set to the logged-in user's ID when inventory_quantity changes.")


    def test_compute_adjustment_value(self):
        """Test computation of adjustment value based on inventory differences."""
        self.product.standard_price = 100.0
        self.stock_quant.inventory_quantity_set = True
        self.stock_quant.inventory_diff_quantity = 5.0
        self.stock_quant.compute_adjustment_value()
        self.assertEqual(
            self.stock_quant.adjustment_value,
            500.0,
            "Adjustment value should be 500.0 (5 * 100)."
        )
        self.stock_quant.inventory_quantity_set = False
        self.stock_quant.compute_adjustment_value()
        self.assertEqual(
            self.stock_quant.adjustment_value,
            0.0,
            "Adjustment value should be 0.0 when inventory_quantity_set is False."
        )


    def test_prepare_account_move_vals(self):
        """Test preparation of account move values."""
        credit_account_id =  self.env['account.account'].create({
            'code': '611011',
            'name': 'CREDIT Account',
        })
        debit_account_id = self.env['account.account'].create({
            'code': '611012',
            'name': 'DEBIT Account',
        })
        journal_id =  self.env['account.journal'].create({
            'name': 'test journal',
            'code': 'TJ',
            'type': 'general',
        })
        qty = 10
        description = "Test Description"
        svl_id = None
        cost = 100.0

        account_move_vals = self.stock_move._prepare_account_move_vals(
            credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost
        )

        self.assertIn('operations_adjustment_reason', account_move_vals)
        self.assertEqual(
            account_move_vals['operations_adjustment_reason'],
            self.operations_adjustment_reason.id,
            "The operations_adjustment_reason should be included in the account move values."
        )

    def test_action_post(self):
        """Test the posting action for an account move."""
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
                'price_unit': self.product.list_price,
            })],
        })
        invoice.stock_move_id = self.stock_move.id
        invoice.action_post()
        self.assertEqual(
            invoice.operations_adjustment_reason,
            self.stock_move.operations_adjustment_reason,
            "The operations_adjustment_reason should match the stock_move's adjustment reason."
        )

    def test_request_approval(self):
        """Test the `request_approval` method """
        self.stock_quant.request_approval()
        self.assertEqual(self.stock_quant.state, 'waiting', "State should be 'waiting' after requesting approval.")
        self.assertNotIn(self.stock_quant.state, ['draft', 'posted', 'cancel'], "State should not be in other states after requesting approval.")

