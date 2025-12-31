# -*- coding: utf-8 -*-
import logging
import base64

from odoo.addons.base.models.ir_actions_report import IrActionsReport
from odoo.exceptions import UserError
from odoo.tests import common, tagged
from .common import TestAccountCommonPayment


_logger = logging.getLogger(__name__)


@tagged("common", "account_payment_remittance_advice")
class TestChoosePartner(TestAccountCommonPayment):
    """Class to test choose partner workflow"""

    def setUp(self):
        super().setUp()
        self.partner_with_email = self.env['res.partner'].create({
            'name': 'Partner With Email',
            'email': 'partner1@example.com',
        })
        self.partner_without_email = self.env['res.partner'].create({
            'name': 'Partner Without Email',
        })
        self.payment1.write({
            'partner_id': self.partner_with_email.id
        })
        self.payment2.write({
            'partner_id': self.partner_without_email.id
        })

        self.choose_partner = self.env['remittance.advice.choose.partner'].create({
            'payment_list': str([self.payment1.id, self.payment2.id]),
        })
        self.line_with_email = self.env['remittance.advice.choose.partner.line'].create({
            'header': self.choose_partner.id,
            'partner_id': self.partner_with_email.id,
            'email': self.partner_with_email.email,
        })
        self.line_without_email = self.env['remittance.advice.choose.partner.line'].create({
            'header': self.choose_partner.id,
            'partner_id': self.partner_without_email.id,
        })

    def test_print_reports(self):
        """Test the `print_reports` method."""
        # Test valid case
        self.line_with_email.print_it = True
        action = self.choose_partner.print_reports()

        # Validate action structure
        self.assertEqual(action['type'], 'ir.actions.report', "The action type should be 'ir.actions.report'.")
        self.assertIn('data', action, "The action should include report data.")
        self.assertIn('viaduct-parameters', action['data'], "'viaduct-parameters' should be in the data.")
        self.assertFalse(action['data']['viaduct-parameters']['all-partners'], "'all-partners' should be False.")
        self.assertIn(self.partner_with_email.id, action['data']['viaduct-parameters']['partner-ids'],
                      "Selected partner ID is missing.")

        # Test case with no selected partners
        self.line_with_email.print_it = False
        self.line_without_email.print_it = False
        with self.assertRaises(UserError, msg="Please add one or more batches"):
            self.choose_partner.print_reports()

    def test_email_reports_render(self):
        """Test that `_render` is called with the correct arguments during email generation."""
        # Patch the `_render` method of `IrActionsReport`
        self.patch(IrActionsReport, '_render', lambda self, *args: (b"PDF data", "application/pdf"))
        # Execute the email_reports method
        result = self.choose_partner.email_reports()
        # Validate that the method executed successfully
        self.assertTrue(result, "The `email_reports` method should return True on success.")
        # Verify that the email was created
        sent_emails = self.env["mail.mail"].search([('email_to', '=', self.partner_with_email.email)])
        self.assertEqual(len(sent_emails), 1, "An email should have been sent to the partner with a valid email.")
        self.assertIn("Remittance Advice", sent_emails.subject, "The email subject should contain 'Remittance Advice'.")
        self.assertTrue(sent_emails.attachment_ids, "The email should have an attachment.")
        # Validate the content of the attachment
        attachment = sent_emails.attachment_ids[0]
        self.assertEqual(attachment.datas, base64.b64encode(b"PDF data"),
                         "The attachment content should match the mocked PDF data.")

    def test_choose_partner_line_defaults(self):
        """Test the default values of `ChoosePartnerLine`."""
        self.assertTrue(self.line_with_email.print_it, "`print_it` should default to True.")
        self.assertFalse(self.line_without_email.email, "The email should be empty for partners without an email.")
