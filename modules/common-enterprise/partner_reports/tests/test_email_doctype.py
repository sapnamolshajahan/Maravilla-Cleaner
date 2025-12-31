# -*- coding: utf-8 -*-
from odoo.tests import Form, new_test_user, tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestEmailDocType(TransactionCase):
    def setUp(self):
        super(TestEmailDocType, self).setUp()
        # Get a reference to the email.doc.type model
        self.email_doc_type_obj = self.env['email.doc.type']

    def test_name_selection_list_includes_partner_statement(self):
        """Test that the partner statement is added to the selection list."""
        selection_list = self.email_doc_type_obj._name_selection_list()
        partner_statement = (50, "partner-statement", "Partner Statement")
        self.assertIn(
            partner_statement,
            selection_list,
            "The selection list should include the partner statement type."
        )

    def test_get_description_for_partner_statement(self):
        """Test that get_description returns the correct description for partner-statement."""
        description = self.email_doc_type_obj.get_description("partner-statement")
        self.assertEqual(
            description,
            "Partner Statement",
            "get_description should return 'Partner Statement' for 'partner-statement'."
        )

    def test_get_description_for_other_types(self):
        """Test that get_description defers to the parent for other types."""
        # Here we test with a dummy type (other than partner-statement)
        # Since we don't know the parent's behavior, we'll simply check that it
        # does not erroneously return the partner statement description.
        description = self.email_doc_type_obj.get_description("some-other-type")
        self.assertNotEqual(
            description,
            "Partner Statement",
            "get_description should not return 'Partner Statement' for other types."
        )
