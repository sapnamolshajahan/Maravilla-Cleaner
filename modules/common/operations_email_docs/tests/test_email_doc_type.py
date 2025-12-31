# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)

NEW_TYPES = {
    "sale_order": (60, "Sale Order"),
    "packing_slip": (70, "Packing Slip"),
}

@tagged("common", "operations_email_docs")
class TestOperationsEmailDocs(common.TransactionCase):
    """Class to test operation related email docs  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.email_doc_type = self.env["email.doc.type"]

    def test_name_selection_list(self):
        """
        Test that NEW_TYPES are included in the name selection list.
        """
        selection_list = self.email_doc_type._name_selection_list()
        # Verify NEW_TYPES are in the selection list
        for key, value in NEW_TYPES.items():
            self.assertIn((value[0], key, value[1]), selection_list,
                          f"Expected {(value[0], key, value[1])} to be in the selection list.")

    def test_get_description(self):
        """
        Test that descriptions are correctly retrieved for NEW_TYPES.
        """
        for key, value in NEW_TYPES.items():
            description = self.email_doc_type.get_description(key)
            self.assertEqual(description, value[1],
                             f"Expected description for {key} to be {value[1]} but got {description}.")
        # Test fallback to the parent method
        other_description = self.email_doc_type.get_description("other")
        self.assertNotEqual(other_description, NEW_TYPES.get("other", [None, None])[1],
                            "Fallback description should not match NEW_TYPES description.")
