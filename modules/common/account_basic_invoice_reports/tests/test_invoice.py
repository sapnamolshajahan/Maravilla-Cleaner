# -*- coding: utf-8 -*-
from mock import MagicMock

from odoo.tests.common import tagged, TransactionCase


@tagged("common", "account_basic_invoice_reports")
class InvoiceTest(TransactionCase):

    def setUp(self):
        super(InvoiceTest, self).setUp()

        invoice = self.env["account.move"]
        invoice._patch_method("__len__", MagicMock(return_value=1))
        invoice._patch_method("ensure_one", MagicMock(return_value=invoice))

    def tearDown(self):
        super(InvoiceTest, self).tearDown()

    def test_get_invoice_report(self):
        invoice = self.env["account.move"]
        self.assertEqual(
            self.env.ref("account_basic_invoice_reports.basic_invoice_viaduct"), invoice.get_invoice_report(),
            "Report mismatch")

    def test_get_sendout_email_template(self):
        invoice = self.env["account.move"]
        self.assertEqual(self.env.ref("account.email_template_edi_invoice"), invoice.get_sendout_email_template())

    def test_printed_report_name(self):
        invoice = self.env["account.move"].new(
            {
                "name": "a/b/c//",
            })
        self.assertEqual("a-b-c--", invoice.get_printed_report_name(), "report name failure")
