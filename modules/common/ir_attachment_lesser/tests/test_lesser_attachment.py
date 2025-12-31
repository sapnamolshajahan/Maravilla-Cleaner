# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import UserError

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "ir_attachment_lesser")
class TestIrAttachmentLesser(common.TransactionCase):
    """Class to test ir.attachment.lesser  workflow for the employee"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.attachment = self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'description': 'A test attachment for LesserAttachment',
            'type': 'binary',
            'datas': b'TestData',  # Simulate file data
            'res_model': 'res.partner',
            'res_id': self.env.ref('base.res_partner_1').id,
            'mimetype': 'text/plain',
        })

    def test_view_creation(self):
        """Test that the LesserAttachment view is created and populated."""
        lesser_attachment = self.env['ir.attachment.lesser'].search([('id', '=', self.attachment.id)])
        self.assertTrue(lesser_attachment,
                        "The LesserAttachment view should include the created ir.attachment record.")
        self.assertEqual(lesser_attachment.name, self.attachment.name,
                         "The name should match between ir.attachment and LesserAttachment.")

    def test_create_restriction(self):
        """Test that creating a LesserAttachment raises a UserError."""
        with self.assertRaises(UserError):
            self.env['ir.attachment.lesser'].create({
                'name': 'Forbidden Creation'
            })

    def test_button_download(self):
        """Test the download button action."""
        lesser_attachment = self.env['ir.attachment.lesser'].search([('id', '=', self.attachment.id)])
        action = lesser_attachment.button_download()
        expected_url = f"/web/content/{lesser_attachment.id}?download=true"
        self.assertEqual(action['url'], expected_url, "The download URL should match the expected format.")
        self.assertEqual(action['type'], 'ir.actions.act_url', "The action type should be 'ir.actions.act_url'.")
        self.assertEqual(action['target'], 'self', "The action target should be 'self'.")
