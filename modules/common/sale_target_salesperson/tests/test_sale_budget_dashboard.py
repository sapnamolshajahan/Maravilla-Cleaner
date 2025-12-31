from odoo.tests.common import TransactionCase
from datetime import date
from odoo.tests import tagged


@tagged("sale_target_salesperson")
class TestSaleBudgetDashboard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
        })
        group_user = self.env.ref('base.group_user')
        with self.env.cr.savepoint():
            self.salesperson = self.env['res.users'].create({
                'name': 'Test Salesperson1',
                'login': 'test_sales1',
                'email': 'test_sales1@example.com',
                'partner_id': self.partner.id,
                'groups_id': [(6, 0, [group_user.id])]
            })

        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
            "user_id" :self.salesperson.id
        })

        self.salesperson = self.env['res.users'].create({
            'name': 'Test Salesperson2',
            'login': 'test_sales2',
            'email': 'test_sales1@example.com',
            'partner_id': self.partner.id,

        })

        self.budget_record = self.env['sale.sale.budget'].create({
            'partner_id': self.salesperson.id,
            'date': date.today(),
            'budget': 10000.0
        })

        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'state': 'draft',
            'invoice_user_id': self.salesperson.id,
            'date': date.today(),
            'amount_untaxed_signed': 5000.0
        })

    def test_run_cron(self):
        """ Test run_cron function creates and updates the dashboard correctly """
        dashboard_model = self.env['sale.budget.dashboard']
        dashboard_model.run_cron()

        dashboard_rec = dashboard_model.search([
            ('salesperson', '=', self.salesperson.id),
            ('period_end_date', '=', self.budget_record.date)
        ])
        self.assertTrue(dashboard_rec, "Dashboard record was not created.")
        self.assertEqual(dashboard_rec.budget, 10000.0, "Budget value is incorrect.")
