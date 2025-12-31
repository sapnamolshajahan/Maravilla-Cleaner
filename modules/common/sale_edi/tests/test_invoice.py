# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tests import tagged


@tagged("sale_edi")
class TestInvoiceEDI(TransactionCase):

    def setUp(self):
        super().setUp()

        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'type': 'sale',
            'code': 'TEST',
            'sequence_id': self.env['ir.sequence'].create({
                'name': 'Test Journal Sequence',
                'code': 'test.journal.sequence',
                'implementation': 'standard',
                'prefix': 'INV/',
                'padding': 5,
            }).id,
        })

        self.partner_with_edi = self.env['res.partner'].create({
            'name': 'EDI Partner',
            'email': 'edi@example.com',
            'edi_generator': "itm",
        })

        self.partner_without_edi = self.env['res.partner'].create({
            'name': 'Non-EDI Partner',
            'email': 'noedi@example.com',
        })

        self.invoice_address = self.env['res.partner'].create({
            'name': 'Invoice Address EDI',
            'email': 'address_edi@example.com',
            'edi_generator': "itm",
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
        })

    def test_action_post_with_edi(self):
        """Test action_post triggers action_resend_edi and updates edi_sent."""
        invoice = self.env['account.move'].create({
            'partner_id': self.partner_with_edi.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })

        invoice.action_post()
        self.assertTrue(invoice.edi_sent, "EDI Sent date should be updated after posting.")

    def test_action_resend_edi_grouping(self):
        """Test action_resend_edi groups invoices by partner."""
        invoice_1 = self.env['account.move'].create({
            'partner_id': self.partner_with_edi.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })

        invoice_2 = self.env['account.move'].create({
            'partner_id': self.partner_with_edi.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2,
                'price_unit': 150.0,
            })]
        })

        invoice_1.action_post()
        invoice_2.action_post()

        self.assertEqual(
            fields.Date.context_today(invoice_1),
            invoice_1.edi_sent,
            "EDI Sent date should match context today after posting invoice 1."
        )
        self.assertEqual(
            fields.Date.context_today(invoice_2),
            invoice_2.edi_sent,
            "EDI Sent date should match context today after posting invoice 2."
        )

    def test_no_edi_sent_without_generator(self):
        """Test that no EDI is sent if neither partner nor address supports EDI."""
        invoice = self.env['account.move'].create({
            'partner_id': self.partner_without_edi.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })

        invoice.action_post()
        self.assertFalse(invoice.edi_sent, "EDI Sent should not be updated if no EDI generator is set.")
