import unittest
from odoo.tests import tagged, TransactionCase
from unittest.mock import MagicMock, patch
from datetime import date
from odoo.addons.sale_edi.models.edi_generator import EDIGenerator, EDIDoc
from odoo.exceptions import UserError


@tagged("sale_edi")
class TestEDIGenerator(TransactionCase):
    test_module = "sale_edi"

    def setUp(self):
        """Set up the mock environment and dependencies."""
        super().setUp()
        self.env = MagicMock()
        self.partner = MagicMock()
        self.partner.name = "Test Partner"
        self.partner.edi_email = "test@example.com"

        self.invoices = MagicMock()
        self.invoices.write = MagicMock()

        self.attachment_model = self.env["ir.attachment"]
        self.mail_model = self.env["mail.mail"]

        class MockEDIGenerator(EDIGenerator):
            def build_edi(self, partner, invoices):
                """Mock the EDI document generation."""
                doc = EDIDoc()
                doc.filename = "test_file.txt"
                doc.subject = "Test Subject"
                doc.body = "This is a test body"
                doc.data = b"Test Data"
                return doc

        self.edi_generator = MockEDIGenerator(self.env)

    @patch("odoo.fields.Date.today", return_value=date(2025, 1, 28))
    def test_send_email_build_edi_not_implemented(self, mock_date_today):
        """Test the successful execution of the send_email function."""
        self.attachment_model.with_context.return_value.create.return_value.id = 1
        self.edi_generator.send_email(self.partner, self.invoices)
        created_attachment = self.attachment_model.with_context().create.call_args[0][0]
        self.assertEqual(created_attachment["name"], "Test Partner - test_file.txt",
                         msg="Attachment name does not match.")
        self.assertEqual(created_attachment["datas"], b"Test Data", msg="Attachment data does not match.")
        self.assertEqual(created_attachment["description"], "EDI file", msg="Attachment description does not match.")
        created_mail = self.mail_model.create.call_args[0][0]
        self.assertEqual(created_mail["email_to"], "test@example.com", msg="Mail recipient (email_to) does not match.")
        self.assertEqual(created_mail["subject"], "Test Subject", msg="Mail subject does not match.")
        self.assertEqual(created_mail["body_html"], "<pre>This is a test body</pre>",
                         msg="Mail body HTML does not match.")
        self.assertEqual(created_mail["attachment_ids"], [(6, 0, [1])], msg="Mail attachments do not match.")
        updated_invoices = self.invoices.write.call_args[0][0]
        self.assertEqual(updated_invoices["edi_sent"], date(2025, 1, 28), msg="Invoice `edi_sent` date does not match.")
        self.assertEqual(updated_invoices["is_move_sent"], True, msg="Invoice `is_move_sent` value does not match.")

    def test_send_email_build_edi_not_implemented(self):
        """Test that an error is raised when build_edi is not implemented in the subclass."""

        class IncompleteEDIGenerator(EDIGenerator):
            pass

        incomplete_edi_generator = IncompleteEDIGenerator(self.env)

        with self.assertRaises(UserError, msg="Expected UserError when `build_edi` is not implemented.") as context:
            incomplete_edi_generator.send_email(self.partner, self.invoices)

        self.assertEqual(str(context.exception), "Builder not written",
                         msg="Error message does not match expected text.")


if __name__ == "__main__":
    unittest.main()