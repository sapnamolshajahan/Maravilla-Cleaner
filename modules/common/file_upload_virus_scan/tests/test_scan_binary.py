# -*- coding: utf-8 -*-
import logging
from unittest.mock import patch
from odoo.tests import HttpCase, tagged
from odoo.addons.website.tools import MockRequest
from odoo.addons.file_upload_virus_scan.controllers.upload_attachment import ScanBinary
from werkzeug.datastructures import FileStorage
from io import BytesIO


_logger = logging.getLogger(__name__)

@tagged("common", "file_upload_virus_scan")
class TestScanBinary(HttpCase):
    def setUp(self):
        super().setUp()
        self.controller = ScanBinary()
        self.company = self.env.company
        self.env.user.company_id = self.company

        self.model = "ir.attachment"
        self.record_id = 1

        # Mock file upload
        self.valid_pdf = FileStorage(
            stream=BytesIO(b"Fake PDF Content"),
            filename="test.pdf",
            content_type="application/pdf"
        )

        self.invalid_exe = FileStorage(
            stream=BytesIO(b"Fake EXE Content"),
            filename="malware.exe",
            content_type="application/x-ms-dos-executable"
        )

        # Default allowed mimetypes for testing
        self.company.allowed_mimetypes = 'text/plain,application/pdf,application/msword'

    def test_get_allowed_mimetypes(self):
        """Ensure get_allowed_mimetypes returns the correct allowed types."""
        expected_mimetypes = {'text/plain', 'application/pdf', 'application/msword'}
        with MockRequest(self.env):
            allowed_mimetypes = self.controller.get_allowed_mimetypes()
            self.assertSetEqual(set(allowed_mimetypes), expected_mimetypes)

    def test_get_allowed_mimetypes_with_blacklist(self):
        """Ensure blacklisted mimetypes are not included even if configured."""
        self.company.allowed_mimetypes += ',application/x-ms-dos-executable'
        with MockRequest(self.env):
            allowed_mimetypes = self.controller.get_allowed_mimetypes()
            self.assertNotIn('application/x-ms-dos-executable', allowed_mimetypes)

    def test_upload_attachment_invalid_mimetype(self):
        """Test uploading a disallowed file format should fail."""
        invalid_file = FileStorage(
            stream=BytesIO(b"Fake executable"),
            filename="malware.exe",
            content_type="application/x-ms-dos-executable"
        )

        with MockRequest(self.env):
            response = self.controller.upload_attachment('res.partner', 1, invalid_file)
        self.assertIn("Skipping the upload", response.get_data(as_text=True))

    def test_upload_attachment_with_virus(self):
        """Simulate a virus scan failure."""
        fake_virus_file = FileStorage(
            stream=BytesIO(b"Infected file"),
            filename="infected.txt",
            content_type="text/plain"
        )

        # Patch scan_file on the IrAttachment class
        with MockRequest(self.env), patch(
                "odoo.addons.file_upload_virus_scan.models.ir_attachment.IrAttachment.scan_file",
                return_value=(False, "Virus detected")
        ):
            response = self.controller.upload_attachment('res.partner', 1, fake_virus_file)
        self.assertIn("contains viruses", response.get_data(as_text=True))
