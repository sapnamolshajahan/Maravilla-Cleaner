from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo import fields
from odoo.tests import tagged
from odoo.addons.sale_edi.models.itm_generator import ItmEDI
from odoo.addons.sale_edi.models.mitre10_generator import Mitre10EDI


@tagged("sale_edi")
class TestPartnerEDI(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
            "edi_email": "test@example.com",
            "edi_reference": "REF001",
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'default_code': 'TP001',
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
            'journal_id': self.journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2,
                'price_unit': 100.0,
            })],
        })

    def test_get_generator_mitre10(self):
        """Test generator for Mitre 10."""
        self.partner.edi_generator = "mitre10"
        result = self.partner.get_generator()
        self.assertIsInstance(result, Mitre10EDI, "Expected Mitre10EDI generator")
        self.assertEqual(result.env, self.env, "Environment mismatch in Mitre10 generator")

    def test_get_generator_itm(self):
        """Test generator for ITM."""
        self.partner.edi_generator = "itm"
        result = self.partner.get_generator()
        self.assertIsInstance(result, ItmEDI, "Expected ItmEDI generator")
        self.assertEqual(result.env, self.env, "Environment mismatch in ITM generator")

    def test_generate_edi_no_email(self):
        """Test that generate_edi logs a warning when edi_email is not set."""
        self.partner.edi_email = False  # Simulate no EDI email
        with self.assertLogs('odoo', level='WARNING') as log:
            self.partner.generate_edi(self.invoice)
        self.assertIn(
            f"EDI unsent, no EDI email address found for {self.partner.name}",
            log.output[0]
        )
