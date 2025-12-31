# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


@tagged("common", "mail_purge")
class TestMailPurge(common.TransactionCase):
    """Class to test mail.mail purge  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.mail_model = self.env["mail.mail"]
        self.config_param = self.env["ir.config_parameter"]

        # Create test emails with different create_date values
        self.email_recent = self.mail_model.create({
            "subject": "Recent Email",
            "body_html": "<p>This is a recent email.</p>",
            "create_date": datetime.now() - timedelta(days=2),
        })
        self.email_old = self.mail_model.create({
            "subject": "Old Email",
            "body_html": "<p>This is an old email.</p>",
            "create_date": datetime.now() - timedelta(days=10),
        })

    def test_do_mail_purge(self):
        """Test that old emails are purged based on the configured purge days."""
        # Set purge days to 5
        self.config_param.set_param("mail_purge.purge_days", 5)
        # Call the purge method
        self.mail_model.do_mail_purge()
        # Check the state of emails
        recent_exists = self.mail_model.search([("id", "=", self.email_recent.id)])
        old_exists = self.mail_model.search([("id", "=", self.email_old.id)])
        self.assertTrue(recent_exists, "Recent email should not be purged.")
        self.assertFalse(old_exists, "Old email should be purged.")

    def test_do_mail_purge_no_purge_days(self):
        """Test that no emails are purged when purge days is zero or not set."""
        # Set purge days to 0
        self.config_param.set_param("mail_purge.purge_days", 0)
        # Call the purge method
        self.mail_model.do_mail_purge()
        # Both emails should still exist
        recent_exists = self.mail_model.search([("id", "=", self.email_recent.id)])
        old_exists = self.mail_model.search([("id", "=", self.email_old.id)])
        self.assertTrue(recent_exists, "Recent email should not be purged.")
        self.assertTrue(old_exists, "Old email should not be purged.")
