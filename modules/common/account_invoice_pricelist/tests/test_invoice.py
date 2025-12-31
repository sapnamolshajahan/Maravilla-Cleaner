# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)

@tagged("common","account_invoice_pricelist")
class TestAccountInvoicePricelist(TransactionCase):
    def setUp(self):
        super(TestAccountInvoicePricelist, self).setUp()

        self.test_pricelist = self.env["product.pricelist"].create({
            "name": "Test Pricelist",
            "currency_id": self.env.ref("base.USD").id,
        })
        self.test_partner = self.env["res.partner"].create({
            "name": "Test Partner",
            "property_product_pricelist": self.test_pricelist.id,
        })

        self.invoice = self.env["account.move"].create({
            "partner_id": self.test_partner.id,
            "move_type": "out_invoice",
        })

    def test_pricelist_onchange_partner_id(self):
        """Test if pricelist is updated when partner_id changes."""
        self.invoice._onchange_partner_id()

        self.env.cr.flush()

        self.assertEqual(
            self.invoice.pricelist, self.test_pricelist,
            "Pricelist should be set based on the partner's property_product_pricelist."
        )

        new_pricelist = self.env["product.pricelist"].create({
            "name": "New Pricelist",
            "currency_id": self.env.ref("base.USD").id,
        })
        new_partner = self.env["res.partner"].create({
            "name": "New Partner",
            "property_product_pricelist": new_pricelist.id,
        })

        self.invoice.partner_id = new_partner
        self.invoice._onchange_partner_id()

        self.assertEqual(
            self.invoice.pricelist, new_pricelist,
            "Pricelist should update when the partner changes to match the new partner's pricelist."
        )