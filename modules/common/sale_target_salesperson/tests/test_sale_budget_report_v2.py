# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tests import tagged


@tagged("sale_target_salesperson")
class TestSalesBudgetReport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
        })
        self.salesperson_1 = self.env['res.users'].create({
            'name': 'Salesperson 1',
            'login': 'sales1',
            'email': 'sales1@example.com'
        })
        self.salesperson_2 = self.env['res.users'].create({
            'name': 'Salesperson 2',
            'login': 'sales2',
            'email': 'sales2@example.com'
        })

        self.team = self.env['crm.team'].create({
            'name': 'Sales Team 1',
            'user_id': self.salesperson_1.id
        })

        self.budget_1 = self.env['sale.sale.budget'].create({
            'partner_id': self.salesperson_1.id,
            'date': fields.Date.today(),
            'budget': 50000.0
        })

        self.sale_order = self.env['sale.order'].create({
            'user_id': self.salesperson_1.id,
            'team_id': self.team.id,
            'date_order': fields.Date.today(),
            'state': 'sale',
            'partner_id':self.partner.id,
            'amount_total': 10000.0
        })

        self.invoice = self.env['account.move'].create({
            'invoice_user_id': self.salesperson_1.id,
            'team_id': self.team.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'amount_total_signed': 8000.0
        })

        self.opportunity = self.env['crm.lead'].create({
            'user_id': self.salesperson_1.id,
            'team_id': self.team.id,
            'expected_revenue': 15000.0,
            'type': 'opportunity',
            'name': 'lead',
            'probability': 80,
            'active': True
        })

    def test_sales_budget_report(self):
        report = self.env['sales.report.budget'].search([('salesperson', '=', self.salesperson_1.id)])
        self.assertTrue(report, "Sales Budget Report was not generated")

        self.assertEqual(report.salesperson.id, self.salesperson_1.id, "Salesperson mismatch")
        self.assertEqual(report.team.id, self.team.id, "CRM Team mismatch")
        self.assertEqual(report.budget, 50000.0, "Budget value incorrect")
        self.assertEqual(report.sale_orders, 10000.0, "Sale orders value incorrect")
        self.assertEqual(report.invoiced, 8000.0, "Invoiced value incorrect")
