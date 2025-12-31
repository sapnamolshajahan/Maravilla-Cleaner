# -*- coding: utf-8 -*-
import logging
from odoo.tests import common, tagged
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


@tagged("common", "massmail_extn")
class TestMassMailWizard(common.TransactionCase):
    """Class to test mass mail wizard workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.mailing_list = self.env['mailing.list'].create({
            'name': 'Test Mailing List',
        })
        # Create some partners
        self.partner1 = self.env['res.partner'].create({
            'name': 'Partner 1',
            'email': 'partner1@example.com',
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Partner 2',
            'email': 'partner2@example.com',
            'edm_opt_out': True,  # This partner should be excluded
        })
        self.partner3 = self.env['res.partner'].create({
            'name': 'Partner 3',
            'email': 'partner3@example.com',
        })
        # Create a filter (domain to select Partner 1 and Partner 3)
        self.filter = self.env['ir.filters'].create({
            'name': 'Test Filter',
            'model_id': 'res.partner',
            'domain': "[('id', 'in', [%s, %s])]" % (self.partner1.id, self.partner3.id),
        })
        # Create a transient model instance
        self.mass_mail_list = self.env['mass.mail.list'].create({
            'name': self.mailing_list.id,
            'mailing_model_id': self.env['ir.model']._get_id('res.partner'),
            'filter_id': self.filter.id,
            'mailing_domain': "[]"
        })

    def test_build_list(self):
        """Test the build_list method."""
        # Execute the method
        self.mass_mail_list.mailing_domain = "[('id', 'in', [%s, %s])]" % (self.partner1.id, self.partner3.id)
        self.mass_mail_list.build_list()
        mailing_contacts = self.env['mailing.contact'].search([('list_ids', 'in', self.mailing_list.id)])
        # Validate that only Partner 1 and Partner 3 were added to the mailing list
        self.assertEqual(len(mailing_contacts), 2, "Only two partners should be added to the mailing list")
        self.assertTrue(
            all(contact.email in ['partner1@example.com', 'partner3@example.com'] for contact in mailing_contacts),
            "Incorrect partners added to the mailing list"
        )

    def test_build_list_no_partner_field(self):
        """Test the error when the model does not have a mapped partner field."""
        # Create a new transient model with a mailing model that lacks a mapped partner field

        mass_mail_list_no_partner = self.env['mass.mail.list'].create({
            'name': self.mailing_list.id,
            'mailing_model_id': self.env['ir.model']._get_id('account.journal'),
            'mailing_domain': "[]",  # Empty domain
        })
        with self.assertRaises(UserError):
            mass_mail_list_no_partner.build_list()

    def test_onchange_filter_id(self):
        self.mass_mail_list.onchange_filter_id()
        self.assertEqual(self.mass_mail_list.mailing_domain, self.mass_mail_list.filter_id.domain)
        self.assertEqual(self.mass_mail_list.mailing_model_real, self.mass_mail_list.mailing_model_name)
