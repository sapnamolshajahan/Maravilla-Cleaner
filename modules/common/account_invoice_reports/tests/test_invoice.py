# -*- coding: utf-8 -*-
from mock import MagicMock
from odoo.addons.base_testing.tests.transaction_case import EziTransactionCase

from ..models.invoice import INVOICE_REPORT


class InvoiceTest(EziTransactionCase):

    def setUp(self):
        super(InvoiceTest, self).setUp()

        invoice = self.env["account.invoice"]
        invoice._patch_method("__len__", MagicMock(return_value=1))
        invoice._patch_method("ensure_one", MagicMock(return_value=invoice))

    def tearDown(self):
        super(InvoiceTest, self).tearDown()

    def test_get_invoice_report(self):
        invoice = self.env["account.invoice"]
        self.assertEquals(INVOICE_REPORT, invoice.get_invoice_report(), "Report name mismatch")

    def test_invoice_print(self):
        invoice = self.env["account.invoice"]
        result = invoice.invoice_print()

        # self.assertTrue(invoice.sent, "unset sent")
        self.assertEquals(result["report_type"], "viaduct", "viaduct type unset")
        self.assertEqual(result["report_name"], INVOICE_REPORT, "report name mismatch")
