# -*- coding: utf-8 -*-
import logging

from dateutil.relativedelta import relativedelta
from odoo.tests import common, tagged
from odoo import fields
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


@tagged("common", "sale_analysis_by_account_owner")
class TestSaleAnalysisReport(common.TransactionCase):
    """Class to test sale analysis report in monthly,quarterly base"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.category_1 = self.env['product.category'].create({'name': 'Category 1'})
        self.category_2 = self.env['product.category'].create({'name': 'Category 2'})
        self.product_1 = self.env['product.product'].create({
            'name': 'Product 1',
            'categ_id': self.category_1.id
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'Product 2',
            'categ_id': self.category_2.id
        })
        self.sale_order_1 = self.env.ref('sale.sale_order_1')
        self.sale_order_line_1 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_1.id,
            'product_id': self.product_1.id,
            'price_total': 100.0,
        })

        self.sale_order_2 = self.env.ref('sale.sale_order_2')
        self.sale_order_line_2 = self.env['sale.order.line'].create({
            'order_id': self.sale_order_2.id,
            'product_id': self.product_2.id,
            'price_total': 200.0,
        })
        self.report_wizard = self.env['sale.analysis.report'].create({
            'period_start': fields.Date.today(),
            'period_to': fields.Date.today() + relativedelta(days=100),
            'group_by_category': True,
        })
        sequence = self.env['ir.sequence'].create({
            'name': 'Journal Sequence',
            'implementation': 'no_gap',
            'prefix': 'BIL/',
            'padding': 5,
        })
        self.sale_order_1.action_confirm()
        self.sale_order_2.action_confirm()
        self.invoice_1 = self.sale_order_1._create_invoices()
        self.invoice_2 = self.sale_order_2._create_invoices()
        self.invoice_1.journal_id.write({
            'sequence_id': sequence.id
        })
        self.invoice_2.journal_id.write({
            'sequence_id': sequence.id
        })

    def test_quarterly_report_get_lines(self):
        """Test that the report returns correct category-grouped data in quarter base"""
        self.report_wizard.run_report()
        with self.assertRaises(UserError):
            self.env["quarterly.sale.analysis.report.categorygroup"].get_lines(self.report_wizard)
        self.invoice_1.action_post()
        self.invoice_2.action_post()
        with self.env.cr.savepoint():
            quarter_group_report_lines = self.env["quarterly.sale.analysis.report.categorygroup"].get_lines(self.report_wizard)
            self.assertTrue(quarter_group_report_lines, "The report lines should not be empty")
            categories = set(line['category_name'] for line in quarter_group_report_lines if 'category_name' in line)
            # Ensure the expected category exists in the report
            self.assertIn('Category 1', categories)
            self.assertIn('Category 2', categories)

            # group_category False report

        self.report_wizard.group_by_category = False
        report = self.report_wizard.run_report()
        with self.env.cr.savepoint():
            nogroup_quarter_report_lines = self.env["quarterly.sale.analysis.report.nogroup"].get_lines(self.report_wizard)
            self.assertTrue(nogroup_quarter_report_lines, "The report lines should not be empty")
            account_names = set(line['account_name'] for line in nogroup_quarter_report_lines if 'account_name' in line)
            total_values = {line['account_name']: line['total_actual'] for line in nogroup_quarter_report_lines if
                            'account_name' in line}
            # Expected accounts should be present
            self.assertIn('Deco Addict', account_names)
            # Expected totals should match
            self.assertEqual(total_values.get('Deco Addict'), 1.0, "Deco Addict total should be 1.0")

    def test_monthly_report_get_lines(self):
        """Test that the report returns correct category-grouped data in month base"""
        self.report_wizard.report_type = 'monthly'
        self.report_wizard.run_report()
        with self.assertRaises(UserError):
            self.env["sale.analysis.report.categorygroup"].get_lines(self.report_wizard)
        self.invoice_1.action_post()
        self.invoice_2.action_post()
        with self.env.cr.savepoint():
            monthly_group_report_lines = self.env["sale.analysis.report.categorygroup"].get_lines(self.report_wizard)
            self.assertTrue(monthly_group_report_lines, "The report lines should not be empty")
            categories = set(line['category_name'] for line in monthly_group_report_lines if 'category_name' in line)
            # Ensure the expected category exists in the report
            self.assertIn('Category 1', categories)
            self.assertIn('Category 2', categories)

       # group_category False report

        self.report_wizard.group_by_category = False
        self.report_wizard.run_report()
        with self.env.cr.savepoint():
            nogroup_report = self.env["sale.analysis.report.nogroup"].get_lines(self.report_wizard)
            self.assertTrue(nogroup_report, "The report lines should not be empty")
            account_names = set(line['account_name'] for line in nogroup_report if 'account_name' in line)
            total_values = {line['account_name']: line['total_actual'] for line in nogroup_report if 'account_name' in line}
            # Expected accounts should be present
            self.assertIn('Deco Addict', account_names)
            self.assertIn('Ready Mat', account_names)
            # Expected totals should match
            self.assertEqual(total_values.get('Deco Addict'), 1.0, "Deco Addict total should be 1.0")
