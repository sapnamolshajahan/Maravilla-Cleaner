# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("common", "purchase_alternate_shipping_address")
class TestResConfigSettings(TransactionCase):
    def setUp(self):
        super(TestResConfigSettings, self).setUp()
        self.company = self.env.company

    def test_show_hide_alt_po_address_field(self):
        """Test if the show_hide_alt_po_address field updates the company setting."""

        settings = self.env['res.config.settings'].create({
            'show_hide_alt_po_address': True,
        })

        self.company.write({'show_hide_alt_po_address': False})
        self.assertFalse(self.company.show_hide_alt_po_address)

        settings.set_values()

        self.cr.flush()
        self.company._invalidate_cache()

        self.assertTrue(self.company.show_hide_alt_po_address)

        settings.write({'show_hide_alt_po_address': False})
        settings.set_values()

        self.cr.flush()
        self.company._invalidate_cache()
        self.assertFalse(self.company.show_hide_alt_po_address)