# -*- coding: utf-8 -*-
import logging
from odoo.tools.config import config
from unittest.mock import patch

from odoo.tests import common, tagged

EMAIL_NOTIFICATION_ADDRESS = 'task_notification_from_address'
EMAIL_NOTIFICATION_PREFIX = 'task_notification_system_prefix'

_logger = logging.getLogger(__name__)


@tagged("common", "email_notification")
class TestMailNotification(common.TransactionCase):
    """Class to test mail.notification   workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.partner = self.env.ref('base.res_partner_12')
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@example.com',
            'partner_id': self.partner.id,
        })
        self.email_notification = self.env['email.notification'].create({
            'user_id': self.user.id,
        })

    @patch('odoo.tools.config.get_misc')
    def test_get_notification_fields_with_config(self, mock_get_misc):
        """Test _get_notification_fields retrieves values from configuration."""
        # Mock the config.get_misc method to return test values
        mock_get_misc.side_effect = lambda section, key, default: {
            (EMAIL_NOTIFICATION_PREFIX, 'tcs'): 'PREFIX_',
            (EMAIL_NOTIFICATION_ADDRESS, 'tcs'): 'test@example.com',
        }.get((key, section), default)

        self.email_notification._get_notification_fields()

        # Validate that the fields are set correctly
        self.assertEqual(self.email_notification.notification_email_prefix, 'PREFIX_')
        self.assertEqual(self.email_notification.notification_from_address, 'test@example.com')
