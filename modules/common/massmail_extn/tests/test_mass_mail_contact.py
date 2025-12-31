# -*- coding: utf-8 -*-
import logging
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "massmail_extn")
class TestMassMailContact(common.TransactionCase):
    """Class to test mass mail contact workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test.partner@example.com',
        })

        # Create a mailing contact linked to the partner
        self.mailing_contact = self.env['mailing.contact'].create({
            'email': 'ma.test.new.1@example.com',
            'name': 'MATest_new_1',
            'partner_id': self.partner.id,
        })

    def test_message_get_default_recipients(self):
        """Test the _message_get_default_recipients method."""
        recipients = self.mailing_contact._message_get_default_recipients()
        # Expected result
        expected_recipients = {
            self.mailing_contact.id: {
                'partner_ids': [self.partner.id],
                'email_to': 'ma.test.new.1@example.com',
                'email_cc': False,
            }
        }
        # Assert that the output matches the expected result
        self.assertDictEqual(
            recipients,
            expected_recipients,
            "The _message_get_default_recipients method did not return the expected output."
        )
