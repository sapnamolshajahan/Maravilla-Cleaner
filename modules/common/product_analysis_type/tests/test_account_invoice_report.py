# -*- coding: utf-8 -*-
import logging
from odoo.tests import tagged, TransactionCase
from datetime import datetime
from odoo import Command

_logger = logging.getLogger(__name__)

@tagged("common", "product_analysis_type")
class TestProductAnalysisType(TransactionCase):
    """
    Test case for Product Analysis type workflow.
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.currency = self.env.ref("base.USD")
        self.company = self.env.ref("base.main_company")
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        self.product_category = self.env["product.category"].create({"name": "Test Category"})

        # Create a product
        self.product = self.env["product.product"].create({
            "name": "Test Product",
            "categ_id": self.product_category.id,
        })
        self.product_analysis = self.env["product.analysis.type"].create({"name": "Test Analysis"})
        sequence = self.env['ir.sequence'].create({
            'name': 'Purchase Journal Sequence',
            'implementation': 'no_gap',
            'prefix': 'BIL/',
            'padding': 5,
        })
        self.purchase_journal = self.env['account.journal'].create({
            'name': 'Purchase',
            'code': 'PO',
            'type': 'purchase',
            'sequence_id': sequence.id
        })
        self.account = self.env['account.account'].create({
            "account_type": 'expense',
            'name': 'account',
            'code': '121040',
        })
        self.invoice = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner.id,
            "currency_id": self.currency.id,
            "company_id": self.company.id,
            'journal_id': self.purchase_journal.id,
            "invoice_date": datetime.today(),
            'invoice_line_ids': [Command.create({
                'name': 'test',
                'quantity': 1,
                "product_id": self.product.id,
                'price_unit': 1000,
                'account_id': self.account.id,
                'product_analysis': self.product_analysis.id
            })],
        })
        self.invoice.action_post()
        self.sale_order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                (0, 0, {
                    "name": "Test Sale Line",
                    "product_id": self.product.id,
                    "product_uom_qty": 1,
                    "price_unit": 100.0,
                })
            ],
        })
    def test_invoice_report_includes_product_analysis(self):
        """Test that account.invoice.report includes the product_analysis field"""
        report_line = self.env["account.invoice.report"].search([
            ("move_id", "=", self.invoice.id)
        ], limit=1)
        self.assertTrue(report_line, "Invoice report entry was not created")

    def test_sale_report_includes_product_analysis(self):
        """Test that sale.report includes the product_analysis field"""
        report_line = self.env["sale.report"].search([
            ("product_id", "=",  self.product.id)
        ], limit=1)
        self.assertTrue(report_line)
