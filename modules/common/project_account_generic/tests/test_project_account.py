# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "project_account")
class TestProjectAccount(common.TransactionCase):
    """Class to test project and account  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.project = self.env.ref('project.project_project_1')
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('product.product_product_6')
        self.account = self.env['account.account'].create([{'code': '1014040', 'name': 'A',
                                                            'account_type': 'asset_cash'}])
        analytic_plan = self.env['account.analytic.plan'].create({'name': 'Plan Test', 'company_id': False})
        self.analytic_account_manual = self.env['account.analytic.account'].create({'name': 'default',
                                                                                    'plan_id': analytic_plan.id})
        analytic_distribution_manual = {str(self.analytic_account_manual.id): 100}
        self.sale_journal = self.env["account.journal"].create({
            'name': "Test Sales Journal",
            'company_id': self.env.ref('base.main_company').id,
            'type': "sale",
            'code': "S0002",
        })
        self.purchase_journal = self.env["account.journal"].create({
            'name': "Test Purchase Journal",
            'company_id': self.env.ref('base.main_company').id,
            'type': "purchase",
            'code': "P0002",
        })
        self.customer_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.sale_journal.id,
            'partner_id': self.partner.id,
            'invoice_date': '2023-01-21',
            'date': '2023-01-21',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 40.0,
                'name': 'product test 1',
                'discount': 10.00,
                'price_unit': 2.27,
                'account_id': self.account.id,
                'analytic_distribution': analytic_distribution_manual,
                'tax_ids': [],
            })]
        })
        _logger.info("Created invoice move_type out_invoice %s" % self.customer_invoice)
        self.supplier_invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'journal_id': self.purchase_journal.id,
            'partner_id': self.partner.id,
            'invoice_date': '2023-01-21',
            'date': '2023-01-21',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 40.0,
                'name': 'product test 1',
                'discount': 10.00,
                'price_unit': 2.27,
                'tax_ids': [],
            })]
        })
        _logger.info("Created invoice move_type in_invoice %s" % self.supplier_invoice)

    def test_project_account_action_changes(self):
        """
         Check different action changes in  project related to account
        """
        # Check customer_invoice_count and supplier_invoice_count
        self.project._calc_invoices()
        project_without_customer_invoice = self.project.action_view_customer_invoices()
        self.assertEqual(project_without_customer_invoice['params'].get('title'), 'No Customer Invoices')
        self.assertEqual(project_without_customer_invoice['params'].get('message'), 'There are no customer invoices'
                                                                                    ' in this project')
        project_without_supplier_invoice = self.project.action_view_supplier_invoices()
        self.assertEqual(project_without_supplier_invoice['params'].get('title'), 'No Supplier Invoices')
        self.assertEqual(project_without_supplier_invoice['params'].get('message'), 'There are no supplier invoices'
                                                                                    ' in this project')
        self.assertEqual(self.project.customer_invoice_count, 0)
        self.assertEqual(self.project.supplier_invoice_count, 0)
        self.project.write({
            'customer_invoices': [[6, 0, [self.customer_invoice.id]]],
            'supplier_invoices': [[6, 0, [self.supplier_invoice.id]]],
        })
        # Check project wih customer and supplier invoice changes
        self.project._calc_invoices()
        self.assertEqual(self.project.customer_invoice_count, 1)
        self.assertEqual(self.project.supplier_invoice_count, 1)
        project_with_customer_invoice = self.project.action_view_customer_invoices()
        self.assertEqual(self.project.customer_invoices.ids, project_with_customer_invoice.get('domain')[0][2])
        self.assertEqual(self.project.customer_invoices.id, project_with_customer_invoice.get('res_id'))
        project_with_supplier_invoice = self.project.action_view_supplier_invoices()
        self.assertEqual(self.project.supplier_invoices.ids, project_with_supplier_invoice.get('domain')[0][2])
        self.assertEqual(self.project.supplier_invoices.id, project_with_supplier_invoice.get('res_id'))

    def test_account_project_changes(self):
        """
        Check analytic account changes based on project
        """
        self.assertFalse(self.customer_invoice.analytic_account_id)
        self.customer_invoice.line_ids._create_analytic_lines()
        self.customer_invoice.calc_analytic_account()
        self.assertEqual(self.customer_invoice.analytic_account_id, self.customer_invoice.line_ids.
                         analytic_line_ids.account_id)
        # Check project in account move
        self.supplier_invoice.write({
            "project_id": self.project.id
        })
        self.supplier_invoice._post()  # Check with project directly
        self.assertEqual(self.project.id, self.supplier_invoice.project_id.id)
        self.project.write({
            "analytic_account_id": self.customer_invoice.line_ids.analytic_line_ids.account_id.id
        })
        self.customer_invoice._post()  # If no project check with analytic account id
        self.assertEqual(self.project.id, self.customer_invoice.project_id.id)
