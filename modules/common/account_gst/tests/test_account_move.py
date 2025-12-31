# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

@tagged("common","account_gst")
class TestAccountMove(TransactionCase):
    def setUp(self):
        super(TestAccountMove, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner'
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test Tax 10%',
            'amount': 10.0,
            'type_tax_use': 'sale',
            'price_include': False
        })
        self.journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'lst_price': 100.0,
        })

    def test_action_post_valid_tax(self):
        """Test posting an invoice with valid tax calculation"""
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Line',
                'quantity': 1.0,
                'price_unit': 100.0,
                'discount': 0.0,
                'tax_ids': [(6, 0, [self.tax.id])]
            })]
        })
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted', "Invoice should be posted successfully")

    def test_action_post_invalid_tax(self):
        """Test posting an invoice with invalid tax calculation should raise an error"""
        self.tax.amount = 200
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Line',
                'quantity': 1.0,
                'price_unit': 100.0,
                'discount': 0.0,
                'tax_ids': [(6, 0, [self.tax.id])]
            })]
        })
        with self.assertRaises(UserError):
            invoice.action_post()

