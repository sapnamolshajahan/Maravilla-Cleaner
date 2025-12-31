from odoo.tests import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import tagged

@tagged('res_partner_credit_limit')
class TestSaleOrder(TransactionCase):

    def setUp(self):
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'credit_limit': 1000,
            'over_credit': False,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
            'list_price': 200,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 5, 'price_unit': 200})]
        })

    def test_check_credit_limit_skip_credit_check(self):
        """Test that credit limit check is skipped when context 'skip_credit_check' is set."""
        self.sale_order.with_context(skip_credit_check=True).check_credit_limit()

    def test_check_credit_limit_over_credit(self):
        """Test that credit check is skipped if the partner is over credit."""
        self.partner.write({'over_credit': True})
        self.sale_order.check_credit_limit()
        self.assertEqual(self.partner.over_credit, True)

    def test_check_credit_limit_blocked_customer(self):
        """Test that an error is raised if the customer is blocked."""
        self.partner.write({'warning_type': 'blocked'})
        with self.assertRaises(UserError):
            self.sale_order.check_credit_limit()

    def test_action_confirm_without_error(self):
        """Test that action_confirm works without error if credit check passes."""
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, 'sale')
