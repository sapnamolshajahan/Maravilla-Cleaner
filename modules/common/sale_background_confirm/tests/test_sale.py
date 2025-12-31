# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError
from odoo import fields


@tagged('common', 'sale_background_confirm')
class TestSaleOrder(TransactionCase):

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.SaleOrder = self.env['sale.order']
        self.sale_order = self.SaleOrder.create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'order_line': [
                fields.Command.create({
                    'name': 'Test Product',
                    'product_id': self.env.ref('product.product_product_4').id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                })
            ]
        })

    def test_get_selection_name(self):
        """Test the selection name retrieval method."""
        name = self.sale_order.get_selection_name(self.env['sale.order'], 'queued_state', 'queued')
        self.assertEqual(name, 'Queued for Processing')

    def test_action_confirm_queued_below_threshold(self):
        """Test sale order confirmation when below the threshold."""
        self.env.company.auto_background_sale_threshold = 10  # Set a high threshold
        self.sale_order.action_confirm_queued()
        self.assertEqual(self.sale_order.state, 'sale')

    def test_action_reset_queued_processing(self):
        """Test resetting a queued order."""
        self.sale_order.state = 'sent'
        self.sale_order.write({'queued_state': 'queued'})
        self.sale_order.action_reset_queued_processing()
        self.assertEqual(self.sale_order.state, 'draft')
        self.assertFalse(self.sale_order.bg_task_id)
        self.assertFalse(self.sale_order.queued_state)

    def test_action_confirm_queued_already_confirmed(self):
        """Ensure confirmation is blocked for already confirmed orders."""
        self.sale_order.write({'queued_state': 'queued', 'state': 'sale'})
        with self.assertRaises(UserError):
            self.sale_order.action_confirm_queued()


class TestComputeBgTaskState(TransactionCase):

    def setUp(self):
        super(TestComputeBgTaskState, self).setUp()
        self.so_model = self.env['sale.order']

    def test_compute_bg_task_state_without_task_id(self):
        so = self.so_model.create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'bg_task_id': False
        })
        so._compute_bg_task_state()
        self.assertFalse(so.bg_task_state)


class TestResConfigSettings(TransactionCase):
    def setUp(self):
        super(TestResConfigSettings, self).setUp()
        self.company = self.env.company
        self.config = self.env['res.config.settings'].create({})

    def test_get_values(self):
        """Test that get_values retrieves the correct threshold from the company."""
        self.company.auto_background_sale_threshold = 10
        config_values = self.config.get_values()
        self.assertEqual(config_values.get('auto_background_sale_threshold'), 10,
                         "get_values should return the correct threshold value")

    def test_set_values(self):
        """Test that set_values updates the company threshold correctly."""
        self.config.auto_background_sale_threshold = 15
        self.config.set_values()
        self.assertEqual(self.company.auto_background_sale_threshold, 15,
                         "set_values should correctly update the company's threshold")
