# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged("common", "mail_block_internal_notification")
class TestMailNotification(common.TransactionCase):
    """Class to test mail.notification workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.test_model = self.env['ir.model'].create({
            'name': 'Test Model',
            'model': 'x_test_model',
            'block_internal_notification': False
        })
        self.mail_message = self.env['mail.message'].create({
            'model': self.test_model.model,
            'message_type': 'user_notification',
            'body': 'Test Message',
        })
        self.test_model_unrelated = self.env['ir.model'].create({
            'name': 'Unrelated Model',
            'model': 'x_unrelated_model',
        })
        self.other_message = self.env['mail.message'].create({
            'model': self.test_model_unrelated.model,
            'message_type': 'notification',
            'body': 'Other Test Message',
        })

    def test_mail_notification_create(self):
        notification_vals = [
            {'mail_message_id': self.mail_message.id, 'res_partner_id': 1},
            {'mail_message_id': self.other_message.id, 'res_partner_id': 1},
        ]
        notifications = self.env['mail.notification'].create(notification_vals)
        if self.test_model.block_internal_notification:
            self.assertEqual(len(notifications), 1, "Notifications should exclude blocked internal notifications.")
            self.assertNotIn(self.mail_message.id, notifications.mapped('mail_message_id'),
                             "Blocked internal notification message shouldn't exist.")
        else:
            self.assertEqual(len(notifications), 2, "Both notifications should be created when not blocked.")
        for notification in notifications:
            self.assertIn(notification.mail_message_id, [self.mail_message, self.other_message],
                          "Notification should belong to a valid message.")
