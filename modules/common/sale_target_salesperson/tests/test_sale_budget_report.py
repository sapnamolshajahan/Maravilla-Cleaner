from odoo.tests.common import TransactionCase
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("sale_target_salesperson")
class TestSaleBudgetReport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
        })
        group_user = self.env.ref('base.group_user')
        with self.env.cr.savepoint():
            self.salesperson = self.env['res.users'].create({
                'name': 'Test Salesperson',
                'login': 'test_salesperson',
                'email': 'sales@test.com',
                'partner_id': self.partner.id,
                'groups_id': [(6, 0, [group_user.id])]
            })

        self.sale_budget_report_run = self.env['sale.budget.report.run'].create({'name': 'Test Run'})

        self.sale_budget = self.env['sale.sale.budget'].create({
            'partner_id': self.salesperson.id,
            'date': datetime.today(),
            'budget': 10000.0
        })

    def test_build_target(self):
        """Test that build_target creates correct report source entries."""
        self.env['sale.budget.report'].build_target(self.sale_budget_report_run)
        sources = self.env['sale.budget.report.source'].search([('sale_budget_report_run', '=', self.sale_budget_report_run.id)])
        self.assertTrue(sources, "No budget report sources were created")
        self.assertEqual(sources[0].budget, 10000.0, "Budget amount mismatch")

    def test_build_account_move(self):
        """Test that build_account_move updates actual values correctly."""
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Customer Invoices',
                'type': 'sale',
                'code': 'CUSTINV',
                'company_id': self.env.company.id,
            })

        if not journal.sequence_id:
            sequence = self.env['ir.sequence'].create({
                'name': 'Customer Invoice Sequence',
                'code': 'account.move',
                'prefix': 'INV/',
                'padding': 6,
                'company_id': self.env.company.id,
            })
            journal.write({'sequence_id': sequence.id})

        user = self.env['res.users'].search([], limit=1)
        if not user:
            user = self.env['res.users'].create({
                'name': 'Test User',
                'login': 'test_user',
                'email': 'test@example.com',
            })
        partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'user_id': user.id,
        })

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'state': 'draft',
            'partner_id': partner.id,
            'date': datetime.today(),
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'quantity': 1,
                'price_unit': 100.0,
                'name': 'Test Invoice Line',
                'account_id': journal.default_account_id.id or self.env['account.account'].search(
                    [('company_id', '=', self.env.company.id)], limit=1).id,
            })],
        })
        try:
            move.action_post()
        except UserError as e:
            self.fail(f"Invoice posting failed: {e}")

        if not self.sale_budget_report_run:
            self.sale_budget_report_run = self.env['sale.budget.report.run'].create({
                'name': 'Test Run',
                'date_start': datetime.today(),
                'date_end': datetime.today(),
            })
        self.env['sale.budget.report'].build_account_move(self.sale_budget_report_run)
        sources = self.env['sale.budget.report.source'].search([
            ('sale_budget_report_run', '=', self.sale_budget_report_run.id)
        ])
        self.assertTrue(sources, "No report sources found for account moves")
        self.assertEqual(sources[0].actual, 100.0, "Incorrect actual revenue calculated")


    def test_build_quotes(self):
        """Test that build_quotes updates quote values correctly."""
        self.env['sale.order'].create({
            'state': 'draft',
            'partner_id': self.salesperson.partner_id.id,
            'amount_untaxed': 3000.0,
            'date_order': datetime.today()
        })

        self.env['sale.budget.report'].build_quotes(self.sale_budget_report_run)
        sources = self.env['sale.budget.report.source'].search([('sale_budget_report_run', '=', self.sale_budget_report_run.id),('quotes', '=', 3000)])
        self.assertTrue(sources, "No budget report sources found for quotes")
        self.assertEqual(sources.quotes, 3000.0, "Quote amount mismatch")

    def test_build_sale_orders(self):
        """Test that build_sale_orders updates sale order values correctly."""
        self.env['sale.order'].create({
            'state': 'sale',
            'partner_id':  self.salesperson.partner_id.id,
            'amount_untaxed': 7000.0,
            'date_order': datetime.today()
        })

        self.env['sale.budget.report'].build_sale_orders(self.sale_budget_report_run)
        sources = self.env['sale.budget.report.source'].search([('sale_budget_report_run', '=', self.sale_budget_report_run.id),('sale_orders', '=',  7000.0)])
        self.assertTrue(sources, "No budget report sources found for sale orders")
        self.assertEqual(sources.sale_orders, 7000.0, "Sale order amount mismatch")

    def test_build_account_move_target(self):
        """Test that build_account_move_target updates invoiced amounts correctly."""
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Customer Invoices',
                'type': 'sale',
                'code': 'CUSTINV',
                'company_id': self.env.company.id,
            })

        if not journal.sequence_id:
            sequence = self.env['ir.sequence'].create({
                'name': 'Customer Invoice Sequence',
                'code': 'account.move',
                'prefix': 'INV/',
                'padding': 6,
                'company_id': self.env.company.id,
            })
            journal.write({'sequence_id': sequence.id})

        user = self.env['res.users'].search([], limit=1)
        if not user:
            user = self.env['res.users'].create({
                'name': 'Test User',
                'login': 'test_user',
                'email': 'test@example.com',
            })
        partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'user_id': user.id,
        })

        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'state': 'draft',
            'partner_id': partner.id,
            'date': datetime.today(),
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'quantity': 1,
                'price_unit': 4000.0,
                'name': 'Test Invoice Line',
                'account_id': journal.default_account_id.id or self.env['account.account'].search(
                    [('company_id', '=', self.env.company.id)], limit=1).id,
            })],
        })
        try:
            move.action_post()
        except UserError as e:
            self.fail(f"Invoice posting failed: {e}")
        if not self.sale_budget_report_run:
            self.sale_budget_report_run = self.env['sale.budget.report.run'].create({
                'name': 'Test Run',
                'date_start': datetime.today(),
                'date_end': datetime.today(),
            })

        self.env['sale.budget.report'].build_account_move_target(self.sale_budget_report_run)
        sources = self.env['sale.budget.report.source'].search([
            ('sale_budget_report_run', '=', self.sale_budget_report_run.id)
        ])
        self.assertTrue(sources, "No budget report sources found for invoiced values")
        self.assertEqual(sources[0].invoiced, 4000.0, "Invoiced amount mismatch")

    def test_query_generation(self):
        """Test that _query returns a valid SQL query."""
        report = self.env['sale.budget.report']
        sql_query = report._query()
        self.assertIn('SELECT', sql_query, "Generated query does not contain SELECT statement")
