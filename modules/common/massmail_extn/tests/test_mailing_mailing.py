# -*- coding: utf-8 -*-
import logging
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "massmail_extn")
class TestMassMailing(common.TransactionCase):
    """Class to test mass mail contact workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        MailServer = self.env['ir.mail_server']
        Company = self.env.user.company_id
        # Create a test mail server
        self.mail_server = MailServer.create({
            'name': 'Test Server',
            'smtp_host': 'smtp.test.com',
            'smtp_port': 25,
            'smtp_user': 'test@test.com',
            'smtp_pass': '123',
        })
        Company.marketing_mail_server = self.mail_server
        self.env['ir.config_parameter'].sudo().set_param('mass_mailing.outgoing_mail_server', str(self.mail_server.id))
        self.env['ir.config_parameter'].sudo().set_param('mass_mailing.mail_server_id', str(self.mail_server.id))

    def test_compute_mail_server_available(self):
        mailing = self.env['mailing.mailing'].create({
            'name': 'Test Campaign',
            'subject': 'some subject',
        })
        mailing._compute_mail_server_available()
        self.assertTrue(mailing.mail_server_available)

    def test_get_default_mail_server_id(self):
        mailing = self.env['mailing.mailing'].new({})
        fallback_mail_server = self.env['ir.config_parameter'].sudo().get_param('mass_mailing.mail_server_id')
        self.assertNotEqual(fallback_mail_server, self.mail_server.id)
        mailing._get_default_mail_server_id()
        self.assertEqual(int(fallback_mail_server), self.mail_server.id)
