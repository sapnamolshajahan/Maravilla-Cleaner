# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "mail_utils")
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
        fake_email = self.env['mail.message'].create({
            'model':  self.partner._name,
            'res_id':  self.partner.id,
            'subject': 'Public Discussion',
            'message_type': 'email',
            'subtype_id': self.env.ref('mail.mt_comment').id,
        })
        self.mail_notification = self.env['mail.notification'].create({
            'res_partner_id': self.partner.id,
            'is_read': False,
            'mail_message_id': fake_email.id,
        })

    def test_set_user(self):
        """Test that the user_id is correctly computed based on res_partner_id."""
        self.mail_notification._set_user()
        self.assertEqual(self.mail_notification.user_id,self.user,
                         "The user_id should match the user associated with the partner.")
        # Change the partner and verify user_id is updated
        new_partner = self.env.ref('base.res_partner_4')
        self.mail_notification.res_partner_id = new_partner
        self.mail_notification._set_user()
        self.assertFalse(self.mail_notification.user_id,
                         "The user_id should be False if no user is associated with the partner.")

    def test_action_close(self):
        """Test that the action_close method marks the notification as read."""
        self.mail_notification.action_close()
        self.assertTrue(self.mail_notification.is_read,
                        "The notification should be marked as read after calling action_close.")
