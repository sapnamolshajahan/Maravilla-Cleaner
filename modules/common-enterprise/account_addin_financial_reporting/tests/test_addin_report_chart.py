# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.odoo.tests import tagged


@tagged('account_addin_financial_reporting')
class TestAddinReportChart(TransactionCase):

    def setUp(self):
        super(TestAddinReportChart, self).setUp()
        self.company = self.env.ref('base.main_company')

        default_plan = self.env['account.analytic.plan'].create({'name': 'Default'})
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'analytic_account_b',
            'plan_id': default_plan.id,
            'company_id': False,
        })
        self.report_name = self.env['addin.report.name'].create({'name': 'Test Report'})
        self.account_group = self.env['addin.report.account.group'].create({
            'name': 'Test Group',
            'report_name': self.report_name.id
        })

    def test_has_analytic_filter_true(self):
        chart = self.env['addin.report.chart'].create({
            'name': 'Chart With Filter',
            'company_id': self.company.id,
            'type': 'profit-loss',
            'account_group_id': self.account_group.id,
        })

        self.env['addin.report.chart.page'].create({
            'name': 'Page 1',
            'chart_id': chart.id,
            'analytic_account': [(6, 0, [self.analytic_account.id])]
        })
        chart._get_analytic_filter()
        self.assertTrue(chart.has_analytic_filter, "Chart should have analytic filter")

    def test_has_analytic_filter_false(self):
        chart = self.env['addin.report.chart'].create({
            'name': 'Chart Without Filter',
            'company_id': self.company.id,
            'type': 'profit-loss',
            'account_group_id': self.account_group.id,
        })

        self.env['addin.report.chart.page'].create({
            'name': 'Page 1',
            'chart_id': chart.id,
        })

        chart._get_analytic_filter()
        self.assertFalse(chart.has_analytic_filter, "Chart should not have analytic filter")


    def test_write_enforces_output_level(self):
        chart = self.env['addin.report.chart'].create({
            'name': 'Test Chart',
            'company_id': self.company.id,
            'type': 'profit-loss',
            'account_group_id': self.account_group.id,
        })

        chart.write({'type': 'balance-sheet'})
        self.assertEqual(chart.line_output_level_sequence1, 'account',
                         "Write should enforce output level to 'account' for balance sheet")

    def test_onchange_type(self):
        chart = self.env['addin.report.chart'].create({
            'name': 'Test Chart',
            'company_id': self.company.id,
            'type': 'balance-sheet',
            'account_group_id': self.account_group.id,
        })
        chart.onchange_type()
        self.assertEqual(chart.line_output_level_sequence1, 'account',
                         "Balance sheet should enforce 'account' line output level")



