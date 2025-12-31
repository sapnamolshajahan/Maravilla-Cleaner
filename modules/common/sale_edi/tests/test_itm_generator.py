from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.addons.sale_edi.models.itm_generator import ItmEDI

@tagged("sale_edi")
class TestItmEDI(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'street': '123 Test Street',
            'city': 'Test City',
            'zip': '12345',
            'country_id': self.env.ref('base.us').id,
            'vat': 'US123456789',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'default_code': 'TP123',
            'lst_price': 100.0,
        })
        self.location_src = self.env['stock.location'].create({
            'name': 'Source Location',
            'usage': 'internal',
        })
        self.location_dest = self.env['stock.location'].create({
            'name': 'Destination Location',
            'usage': 'internal',
        })
        self.picking_type = self.env['stock.picking.type'].create({
            'name': 'Internal Picking',
            'code': 'internal',
            'use_create_lots': False,
            'use_existing_lots': False,
            'default_location_src_id': self.location_src.id,
            'default_location_dest_id': self.location_dest.id,
            'sequence_code': 1
        })
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'picking_type_id': self.picking_type.id,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 50.0,
            })],
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
            'invoice_date': '2025-01-01',
            'sale_order_id': self.sale_order.id,
            'picking_ids': [(6, 0, [self.picking.id] if self.picking else [])],
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2,
                'price_unit': 100.0,
            })],
        })


    def test_get_itm_customer_code_name_from_invoice(self):
        """Test fetching customer code and name from the invoice."""
        edi_instance = ItmEDI(self.env)
        code, name = edi_instance.get_itm_customer_code_name_from_invoice(self.invoice)

        self.assertEqual(code, 'NOT SET', "Customer VAT should match.")
        self.assertEqual(name, 'NOT SET', "Customer name should match.")

    def test_get_itm_customer_code_name_from_sale_order(self):
        """Test fetching customer code and name from the invoice."""
        edi_instance = ItmEDI(self.env)
        code, name = edi_instance.get_itm_customer_code_name_from_sale_order(self.sale_order)

        self.assertEqual(code, 'NOT SET', "Customer VAT should match.")
        self.assertEqual(name, 'Test Partner', "Customer name should match.")

    def test_get_itm_edi_filename(self):
        """Test generating the EDI filename."""
        edi_instance = ItmEDI(self.env)
        filename = edi_instance.get_itm_edi_filename(self.partner,self.invoice)
        self.assertTrue(filename.endswith('INVOIC.txt'), "Filename should ends with 'INVOIC'.")
        self.invoice.move_type = 'out_refund'
        filename = edi_instance.get_itm_edi_filename(self.partner, self.invoice)
        self.assertTrue(filename.endswith('CREDIT.txt'), "Filename should ends with 'CREDIT'.")

    def test_build_edi(self):
        """Test building the complete EDI document."""
        edi_instance = ItmEDI(self.env)
        edi_doc = edi_instance.build_edi(self.partner, self.invoice)
        self.assertIsNotNone(edi_doc, "EDI document should not be None.")
        filename = edi_doc.filename
        subject = edi_doc.subject
        self.assertIn('INVOIC', filename, "EDI filename should include 'INVOIC'.")
        self.assertIn('ITM EDI', subject, "Subject should reference 'Invoice'.")

    def test_create_itm_edi(self):
        """Test creating EDI data."""
        edi_data = ItmEDI(self.env).create_itm_edi(self.partner, self.invoice)
        self.assertTrue(edi_data, "EDI data should be generated and non-empty.")

    def test_missing_sale_order(self):
        """Test error handling for missing sale order."""
        self.invoice.sale_order_id = False
        with self.assertRaises(UserError, msg="This Invoice/Credit Note does not have an associated sale order"):
            ItmEDI(self.env).create_itm_edi(self.partner, self.invoice)

