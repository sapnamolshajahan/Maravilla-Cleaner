# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged("common", "mail_enable_rc")
class TestIrMailServer(common.TransactionCase):
    """Class to test ir.mail.server workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.test_server = self.env['ir.mail_server'].create({
            'from_filter': 'example_2.com, example_3.com',
            'name': 'Test Server',
            'smtp_host': 'smtp_host',
            'smtp_encryption': 'none',
        })
        _logger.info("test_server %s", self.test_server)

    @patch("odoo.addons.base.models.ir_mail_server.IrMail_Server.send_email", autospec=True)
    @patch("odoo.addons.mail_enable_rc.models.ir_mail_server.ENABLE_SEND", False)
    def test_send_email_disabled(self, mock_super_send_mails):
        """
        Test that send_email does not send emails when ENABLE_SEND is False.
        """
        result = self.test_server.send_email("Test Message")
        self.assertFalse(result, "Email should not be sent when ENABLE_SEND is disabled.")
        mock_super_send_mails.assert_not_called()


    @patch("odoo.addons.mail_enable_rc.models.ir_mail_server.ENABLE_SEND", new=True)
    @patch("odoo.addons.base.models.ir_mail_server.IrMail_Server.send_email", return_value=True)
    def test_send_email_enabled(self, mock_super_send_email):
        """
        Test that send_email proceeds when ENABLE_SEND is True.
        """
        result = self.test_server.send_email("Test Message")
        self.assertTrue(result, "Email should be sent when ENABLE_SEND is enabled.")
        mock_super_send_email.assert_called_once_with("Test Message")
