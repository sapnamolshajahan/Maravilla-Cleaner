from odoo.tests.common import TransactionCase
from odoo.addons.sale_edi.models.mitre10_generator import Mitre10EDI
from odoo import fields
from odoo.tests import tagged


@tagged("sale_edi")
class TestMitre10EDI(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'edi_reference': 'TEST123',
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
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

        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'sale_order_id': self.sale_order.id,
            'journal_id': self.journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.env['product.product'].create({
                    'name': 'Test Product',
                    'default_code': 'TP001',
                }).id,
                'quantity': 2,
                'price_unit': 100.0,
            })],
        })
    def test_get_edi_ref(self):
        edi_ref = Mitre10EDI(self.env).get_edi_ref(self.partner)
        self.assertEqual(edi_ref, 'TEST123', "The EDI reference should match the partner's edi_reference")

    def test_get_m10_customer_code_name_from_sale_order(self):
        code, name = Mitre10EDI(self.env).get_m10_customer_code_name_from_sale_order(self.sale_order)
        self.assertEqual(code, 'TEST123', "The EDI reference from the shipping partner should match")
        self.assertEqual(name, 'Test Partner', "The partner name should match")

    def test_create_mitre10_edi(self):
        edi_data = Mitre10EDI(self.env).create_mitre10_edi(self.partner, [self.invoice])
        self.assertIsInstance(edi_data, bytes, "The EDI data should be returned as bytes")
