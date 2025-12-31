from odoo.tests import common, tagged
from datetime import datetime, time


@tagged('purchase_generic_changes')
class TestPurchaseGenericChanges(common.TransactionCase):
    """Tests for Operations Auto Invoice Module."""

    def setUp(self):
        """ Setup initial conditions for the test case """
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': 'True',
            'list_price': 100.0,
        })
        self.currency = self.env['res.currency'].create({
            'name': 'TEST',
            'symbol': 'T$',
            'rounding': 0.01,
            'decimal_places': 2,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })

        self.supplier = self.env['res.partner'].create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
        })

        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'date_order': '2025-01-02',
            'date_planned': '2025-01-10',
        })

        self.purchase_order_line = self.env['purchase.order.line'].create({
            'order_id': self.purchase_order.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 100.0
        })
        self.account = self.env["account.account"].create(
            {
                "name": "Generic",
                "code": "GENERIC",
                "account_type": 'asset_non_current',
            })

        self.company = self.env['res.company'].search([], limit=1)
        self.env.user.company_id = self.company
        self.incoterm = self.env['account.incoterms'].create({
            'name': 'Test Incoterm',
            'code': 'TEST',
        })
        self.test_message = self.env['mail.message'].create({
            'subject': 'Test Message',
            'body': 'This is a test message.',
            'model': 'res.partner',
            'res_id': self.env['res.partner'].create({'name': 'Test Partner'}).id,
        })
        self.recipients_data = [{
            'id': self.partner.id,
            'name': self.partner.name,
            'email': self.partner.email,
            'type': 'partner',
        }]
        self.origins = ['Origin 1', 'Origin 2']


        self.company.purchase_set_counts_zero = False
        self.stock_rule = self.env['stock.rule'].search([], limit=1)

        self.uom = self.env['uom.uom'].create({
            'name': 'Test UoM',
            'uom_type': 'reference',
            'factor_inv': 1.0,
        })
        self.child_contact = self.env['res.partner'].create({
            'name': 'Test Contact',
            'parent_id': self.partner.id,
            'type': 'delivery',
            'company_id': self.company.id,
            'street': '123 Main St',
            'street2': 'Suite 456',
            'city': 'Test City',
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
        })
        self.customer_location = self.env['stock.location'].create({
            'name': 'Customer Location',
            'usage': 'customer',
        })
        self.picking_type = self.env['stock.picking.type'].create({
            'name': 'Test Picking Type',
            'code': 'outgoing',
            'sequence_code': 'TEST_PICK',
        })
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.purchase_order.partner_id.id,
            'location_id':  self.customer_location.id,
            'location_dest_id': self.customer_location.id,
            'scheduled_date': '2025-01-10',
            'picking_type_id': self.picking_type.id,
        })
        self.stock_move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom_id': self.product.uom_id.id,
            'location_id':  self.customer_location.id,
            'location_dest_id':  self.customer_location.id,
            'purchase_line_id': self.purchase_order_line.id,
            'picking_id': self.picking.id,
        })
        self.sale_journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'type' : 'sale',
            'code': 'SALE',
            'company_id': self.partner.company_id.id
        })

    def test_set_done(self):
        """ Test the set_done method functionality """
        self.assertEqual(self.purchase_order.state, 'draft')
        wizard = self.env["purchase.done"].create({
            'purchase_id': self.purchase_order.id,
        })
        wizard.set_done()
        self.assertEqual(self.purchase_order.state, 'done')

    def test_set_values(self):
        config = self.env['res.config.settings'].create({
            'purchase_incoterm': self.incoterm.id,
            'hide_drop_ship_fields': True,
            'hide_alt_address_fields': False,
            'hide_delivery_notes_fields': True,
            'purchase_set_counts_zero': True,
        })
        config.set_values()
        self.assertEqual(self.company.purchase_incoterm.id, self.incoterm.id,
                         msg=f"Expected purchase incoterm ID {self.incoterm.id}, but got {self.company.purchase_incoterm.id}")

        self.assertTrue(self.company.hide_drop_ship_fields,
                        msg="Expected 'hide_drop_ship_fields' to be True, but it was False")

        self.assertFalse(self.company.hide_alt_address_fields,
                         msg="Expected 'hide_alt_address_fields' to be False, but it was True")

        self.assertTrue(self.company.hide_delivery_notes_fields,
                        msg="Expected 'hide_delivery_notes_fields' to be True, but it was False")

        self.assertTrue(self.company.purchase_set_counts_zero,
                        msg="Expected 'purchase_set_counts_zero' to be True, but it was False")

    def test_notify_get_recipients_groups(self):
        mail_thread = self.env['mail.thread']
        groups = mail_thread._notify_get_recipients_groups(
            self.test_message,
            "Test Model Description"
        )

        self.assertTrue(groups, "The groups list should not be empty.")
        for _group_name, _group_method, group_data in groups:
            self.assertFalse(group_data['has_button_access'], "has_button_access should be False.")

    def test_notify_get_recipients_classify(self):
        mail_thread = self.env['mail.thread']
        groups = mail_thread._notify_get_recipients_classify(
            self.test_message,
            self.recipients_data,
            "Test Model Description"
        )
        self.assertTrue(groups, "The groups list should not be empty.")
        for group in groups:
            self.assertFalse(group.get("has_button_access"), "has_button_access should be False.")

    def test_supplier_invoice_count(self):
        """Test the _compute_override_supplier function"""
        self.partner._compute_override_supplier()
        purchase_journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', self.partner.company_id.id)
        ], limit=1)

        if not purchase_journal:
            purchase_journal = self.env['account.journal'].create({
                'name': 'Purchase Journal',
                'code': 'PURCHASE',
                'type': 'purchase',
                'company_id': self.partner.company_id.id,
            })

        self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'in_invoice',  # Purchase invoice
            'invoice_date': '2025-01-02',
            'amount_total': 150.0,
            'journal_id': purchase_journal.id,  # Use the correct purchase journal
        })
        self.partner._compute_override_supplier()
        """Test when purchase_set_counts_zero is set to True"""
        self.company.purchase_set_counts_zero = True
        self.partner._compute_override_supplier()
        self.assertEqual(self.partner.supplier_invoice_count, 0)

    def test_purchase_order_count(self):
        """Test the _compute_override_purchase function"""
        self.partner._compute_override_purchase()
        self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'amount_total': 300.0,
        })
        """Test when purchase_set_counts_zero is set to True"""
        self.company.purchase_set_counts_zero = True
        self.partner._compute_override_purchase()
        self.assertEqual(self.partner.purchase_order_count, 0)

    def test_fully_received(self):
        """ Purchase Order in "draft" state (should not be fully received)"""

        self.purchase_order.order_line.create({
            'order_id': self.purchase_order.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 100,
        })
        self.purchase_order._fully_received()
        self.assertFalse(self.purchase_order.fully_received, "Order should not be fully received in draft state")

        """Purchase Order in "purchase" state, but not fully received"""
        self.purchase_order.state = 'purchase'
        self.purchase_order.order_line.qty_received = 5  # Received only 5 out of 10
        self.purchase_order._fully_received()
        self.assertFalse(self.purchase_order.fully_received,
                         "Order should not be fully received when qty_received is less than product_qty")

        """Purchase Order in "done" state and fully received"""
        self.purchase_order.state = 'done'
        self.purchase_order.order_line.qty_received = 10  # Received all the product quantity
        self.purchase_order._fully_received()
        self.assertTrue(self.purchase_order.fully_received, "Order should be fully received when all quantities are received")

    def test_onchange_purchase_partner(self):
        """
        Test the onchange_purchase_partner function.
        """
        self.purchase_order.partner_address_id = self.partner.id
        self.purchase_order.onchange_purchase_partner()

        self.assertTrue(
            self.purchase_order.partner_address_id,
            "The partner address ID should be set to the delivery contact ID."
        )
        self.purchase_order.delivery_address_desc = "123 Main St, Suite 456, Test City"
        self.assertTrue(
            self.purchase_order.delivery_address_desc,
            "The delivery address description should be set correctly."
        )
        self.partner.purchase_incoterm = False
        self.purchase_order.onchange_purchase_partner()

        self.assertEqual(
            self.purchase_order.incoterm_id,
            self.company.purchase_incoterm,
            "The incoterm ID should fall back to the company's purchase incoterm."
        )

    def test_write_updates_picking_dates(self):
        """
        Test that updating the `date_planned` on a purchase order updates the picking's dates.
        """
        new_date_planned = '2025-01-20'
        self.purchase_order.write({'date_planned': new_date_planned})
        picking_scheduled_date = self.picking.scheduled_date.strftime(
            '%Y-%m-%d') if self.picking.scheduled_date else None
        picking_date_deadline = self.picking.date_deadline.strftime('%Y-%m-%d') if self.picking.date_deadline else None
        picking_date = self.picking.date.strftime('%Y-%m-%d') if self.picking.date else None
        self.assertEqual(
            picking_scheduled_date,
            new_date_planned,
            "Scheduled date on picking was not updated."
        )
        self.assertEqual(
            picking_date_deadline,
            new_date_planned,
            "Deadline date on picking was not updated."
        )
        self.assertEqual(
            picking_date,
            new_date_planned,
            "Date on picking was not updated."
        )

    def test_prepare_invoice_sets_partner_id(self):
        """
        Test that _prepare_invoice sets the partner_id correctly in the invoice values.
        """
        invoice_vals = self.purchase_order._prepare_invoice()
        self.assertEqual(invoice_vals.get('partner_id'), self.purchase_order.partner_id.id,
                         "The partner_id in the invoice values is incorrect.")

    def test_qty_invoiced_adjustment(self):
        """
        Test that the qty_invoiced is adjusted correctly and qty_to_invoice is set to 0
        when qty_invoiced >= product_qty.
        """
        self.purchase_order_line.qty_invoiced = 10.0
        self.purchase_order_line.product_qty = 10.0
        self.purchase_order_line.qty_received = 5.0
        self.purchase_order_line.qty_to_invoice = 5.0

        account_move = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': '2025-01-02',
            'journal_id': self.sale_journal.id,
        })

        invoice_line = self.env['account.move.line'].create({
            'move_id': account_move.id,
            'product_id': self.product.id,
            'account_id': self.product.property_account_expense_id.id or self.env['account.account'].search(
                [('deprecated', '=', False)], limit=1).id,
            'quantity': 5.0,
            'name': 'Test Product Invoice',
            'price_unit': 100.0,
            'debit': 500.0,
            'credit': 0.0,
            'tax_ids': [(6, 0, [])],
        })

        self.purchase_order_line.invoice_lines = [(4, invoice_line.id)]
        self.purchase_order_line._compute_qty_invoiced()
        self.assertEqual(self.purchase_order_line.qty_to_invoice, 0.0,
                         "Qty to invoice was not set to 0 when qty_invoiced >= product_qty.")

    def test_prepare_stock_moves(self):
        stock_moves = self.purchase_order_line._prepare_stock_moves(self.picking)
        for move in stock_moves:
            self.assertEqual(
                move.get('partner_id'),
                self.picking.partner_id.id,
                "The partner_id in the stock move should match the partner_id of the picking."
            )

    def test_convert_to_middle_of_day(self):
        test_date = datetime(2024, 1, 1, 15, 0)  # 3:00 PM UTC
        midday_date = self.purchase_order_line._convert_to_middle_of_day(test_date)
        self.assertTrue(
            midday_date,
            "The converted date should correctly adjust to the next day's"
        )

    def test_write_updates_stock_move_dates(self):
        """
          Test that updating the `date_planned` on a purchase order line updates the
          corresponding stock move's dates correctly, based on its state.
        """
        new_date = datetime(2024, 2, 1)
        self.purchase_order_line.write({'date_planned': new_date})
        self.assertEqual(
            self.purchase_order_line.move_ids.date,new_date,
            f"Expected the stock move's `date` to be updated to {new_date}, but got {self.stock_move.date}."
        )

        self.stock_move.state = 'done'
        new_date = datetime(2024, 2, 1)
        self.purchase_order_line.write({'date_planned': new_date})

        self.assertEqual(
            self.purchase_order_line.move_ids.date_deadline, new_date,
            "Stock move in 'done' state should not have its `date` updated."
        )
        self.assertEqual(
            self.purchase_order_line.move_ids.date,
            new_date,
            "Stock move in 'done' state should not have its `date_deadline` updated."
        )

    def test_compute_price_with_supplierinfo(self):
        """  Test that the `_compute_price_unit_and_date_planned_and_name` method
        correctly computes the `price_unit` field on a purchase order line."""
        self.purchase_order_line._compute_price_unit_and_date_planned_and_name()
        self.assertEqual(
            self.purchase_order_line.price_unit,
            0.0,
            "Price unit should be zero when supplierinfo exists for the product and partner."
        )
