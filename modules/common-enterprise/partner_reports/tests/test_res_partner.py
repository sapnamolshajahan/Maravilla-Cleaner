# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tests import Form, new_test_user, tagged

# Import the constant for the partner statement type from your module
from ..models.email_doctype import STATEMENT_TYPE

@tagged('post_install', '-at_install')
class TestResPartnerDocs(TransactionCase):
    def setUp(self):
        super(TestResPartnerDocs, self).setUp()
        self.Partner = self.env['res.partner']
        self.EmailDocument = self.env['partner.document.email']
        self.EmailDocType = self.env['email.doc.type']

        # Ensure a record for partner-statement exists
        partner_statement_type = self.EmailDocType.search(
            [('name', '=', STATEMENT_TYPE)], limit=1)
        if not partner_statement_type:
            partner_statement_type = self.EmailDocType.create({
                'name': STATEMENT_TYPE,
                # 'sequence': 50,
                # 'description': "Partner Statement",
            })
        self.partner_statement_type = partner_statement_type

        # Create (or fetch) another document type to test non-matching cases
        other_doc_type = self.EmailDocType.search(
            [('name', '=', 'other-type')], limit=1)
        if not other_doc_type:
            other_doc_type = self.EmailDocType.create({
                'name': 'other-type',
                # 'sequence': 60,
                # 'description': "Other Document",
            })
        self.other_doc_type = other_doc_type

    def test_partner_statement_email_computation(self):
        """Test that partner_statement_email is computed as a comma separated list
        of emails for active partner-statement documents."""
        # Create a partner
        partner = self.Partner.create({
            'name': 'Test Partner',
        })

        # Create two email documents with the partner-statement type (active)
        self.EmailDocument.create({
            'partner_id': partner.id,
            'email': 'active1@example.com',
            'disabled': False,
            'email_doc_type': self.partner_statement_type.id,
        })
        self.EmailDocument.create({
            'partner_id': partner.id,
            'email': 'active2@example.com',
            'disabled': False,
            'email_doc_type': self.partner_statement_type.id,
        })
        # Create one document with partner-statement type but disabled (should be ignored)
        self.EmailDocument.create({
            'partner_id': partner.id,
            'email': 'inactive@example.com',
            'disabled': True,
            'email_doc_type': self.partner_statement_type.id,
        })
        # Create one document with a different type (should be ignored)
        self.EmailDocument.create({
            'partner_id': partner.id,
            'email': 'other@example.com',
            'disabled': False,
            'email_doc_type': self.other_doc_type.id,
        })

        # Invalidate cache to force recomputation
        partner.invalidate_cache()
        computed_email = partner.partner_statement_email

        expected_email = 'active1@example.com,active2@example.com'
        self.assertEqual(
            computed_email,
            expected_email,
            "partner_statement_email should return a comma separated list of active partner-statement document emails."
        )

    def test_partner_statement_email_empty(self):
        """Test that partner_statement_email is empty when no active partner-statement docs exist."""
        # Create a partner
        partner = self.Partner.create({
            'name': 'No Email Partner',
        })

        # Create a document with a non-matching type
        self.EmailDocument.create({
            'partner_id': partner.id,
            'email': 'other@example.com',
            'disabled': False,
            'email_doc_type': self.other_doc_type.id,
        })
        # Create a partner-statement document that is disabled
        self.EmailDocument.create({
            'partner_id': partner.id,
            'email': 'inactive@example.com',
            'disabled': True,
            'email_doc_type': self.partner_statement_type.id,
        })

        partner.invalidate_cache()
        computed_email = partner.partner_statement_email

        self.assertEqual(
            computed_email,
            '',
            "partner_statement_email should be empty if no active partner-statement documents are present."
        )
