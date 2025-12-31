# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged("common", "mail_no_subscribe")
class TestMailThread(common.TransactionCase):
    """Class to test mail.thread extent workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.partner_user = self.env.ref('base.res_partner_12')
        self.partner_customer = self.env.ref('base.res_partner_1')
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser@example.com',
            'partner_id': self.partner_user.id,
        })
        self.company = self.env.company
        self.company.write({
            'exclude_internal': True,
            'exclude_external': False,
        })
        self.test_model = self.env.ref('base.res_partner_2')
        self.mail_follower = self.env['mail.followers'].create({
            'res_model': 'res.partner',
            'res_id': self.test_model.id,  # ID of the partner to follow
            'partner_id': self.partner_customer.id,  # The partner to follow
        })

    def test_insert_followers(self):
        """Test the behavior of `_insert_followers` when internal users are excluded."""
        partner_ids = [self.partner_user.id, self.partner_customer.id]
        self.mail_follower._insert_followers(
            'res.partner', [self.test_model.id], partner_ids
        )
        # Check the followers
        followers = self.mail_follower.search([('res_model', '=', 'res.partner'),
                                            ('res_id', '=', self.test_model.id)])
        partner_ids_followed = followers.mapped('partner_id.id')
        # Verify internal user is excluded and customer is included
        self.assertNotIn(self.partner_user.id, partner_ids_followed, "Internal user should be excluded as a follower.")
        self.assertIn(self.partner_customer.id, partner_ids_followed, "Customer should be included as a follower.")

    def test_notify_get_recipients(self):
        """Test the behavior of `_notify_get_recipients`."""
        # Create a test message
        message = self.env['mail.message'].create({
            'model': 'res.partner',
            'res_id': self.test_model.id,
            'body': 'Test Message',
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'partner_ids': [(4, self.partner_customer.id)]
        })
        # Get recipients
        recipients = self.test_model._notify_get_recipients(message, {})
        # Validate the behavior
        recipient_ids = [rec['id'] for rec in recipients]
        # When `exclude_internal` is True, internal users should be excluded
        self.assertNotIn(self.partner_user.id, recipient_ids, "Internal user should not be a recipient.")
        self.assertIn(self.partner_customer.id, recipient_ids, "Customer should be a recipient.")
