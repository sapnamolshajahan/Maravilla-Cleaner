# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged("common", "mail_enable_rc")
class TestFetchMailServer(common.TransactionCase):
    """Class to test fetchmail.server workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.fetchmail_server = self.env["fetchmail.server"].create({
            "name": "Test Server",
            "server_type": "imap",
            "server": "imap.example.com",
            "port": 993,
            "user": "test@example.com",
        })
        _logger.info("fetchmail_server %s", self.fetchmail_server)

    @patch("odoo.addons.mail.models.fetchmail.FetchmailServer._fetch_mails", autospec=True)
    @patch("odoo.addons.mail_enable_rc.models.fetchmail_server.ENABLE_FETCH", False)
    def test_fetch_mails_disabled(self, mock_super_fetch_mails):
        """
        Test that emails are not fetched when ENABLE_FETCH is False.
        """
        result = self.fetchmail_server._fetch_mails()
        self.assertFalse(
            result,
            "Fetch mails should return False when ENABLE_FETCH is disabled."
        )
        mock_super_fetch_mails.assert_not_called()

    @patch("odoo.addons.mail.models.fetchmail.FetchmailServer._fetch_mails", autospec=True)
    @patch("odoo.addons.mail_enable_rc.models.fetchmail_server.ENABLE_FETCH", True)
    def test_fetch_mails_enabled(self, mock_super_fetch_mails):
        """
        Test that emails are not fetched when ENABLE_FETCH is True.
        """
        result = self.fetchmail_server._fetch_mails()
        self.assertTrue(result, "Fetch mails should proceed when ENABLE_FETCH is enabled.")
        mock_super_fetch_mails.assert_called_once()
