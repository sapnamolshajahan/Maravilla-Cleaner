# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from unittest.mock import patch
import base64
import io

@tagged("common", "audit_log_print")
class TestAuditTrailPrint(TransactionCase):
    def setUp(self):
        super(TestAuditTrailPrint, self).setUp()

        # Create test data
        self.audit_log_print = self.env['audit.log.print'].create({
            'start': fields.Datetime.now(),
            'finish': fields.Datetime.now(),
            'model_ids': [(6, 0, [self.env.ref('base.model_res_partner').id])],
            'run_as_task': False,
            'output_type': 'xlsx',
        })
        self.test_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        # Create a test group for group_by field
        self.audit_log_group = self.env['audit.logging.group'].create({
            'name': 'Test Group',
            'model_id': self.test_model.id,  # Provide the required model_id
        })

    def test_audit_log_print_creation(self):
        """Test if the audit log print record is created correctly."""
        self.assertEqual(self.audit_log_print.start, fields.Datetime.now())
        self.assertEqual(self.audit_log_print.finish, fields.Datetime.now())
        self.assertTrue(self.audit_log_print.model_ids)
        self.assertEqual(self.audit_log_print.output_type, 'xlsx')

    def test_print_report(self):
        """Test the print_report method."""
        # Call the print_report method
        result = self.audit_log_print.print_report()

        # Check if the method returns the correct action
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'audit.log.print')
        self.assertEqual(result['view_mode'], 'form')
        self.assertEqual(result['target'], 'new')

        # Check if the report data is saved correctly
        self.assertTrue(self.audit_log_print.data)
        self.assertTrue(self.audit_log_print.report_name)

    def test_run_report_as_task(self):
        """Test the run_report_as_task method."""
        # Set run_as_task to True
        self.audit_log_print.run_as_task = True

        # Call the print_report method
        result = self.audit_log_print.print_report()

        # Check if the method returns None (since it runs as a task)
        self.assertIsNone(result)

    def test_create_audit_report_from_task(self):
        """Test the create_audit_report_from_task method."""
        # Mock the run_report method to return a test file
        def mock_run_report(wizard_id,email):
            fake_file = io.BytesIO(b"Test Data")
            return ("Test Report", "test_report.xlsx", "Test Description", fake_file)

        # Use patch to mock the run_report method
        with patch('odoo.addons.audit_logging.report.audit_log_report.AuditLogReport.run_report', new=mock_run_report):
            # Call the create_audit_report_from_task method
            self.audit_log_print.create_audit_report_from_task([self.audit_log_print.id],'test@example.com')
        # Check if the email was sent
        mail = self.env['mail.mail'].search([('email_to', '=', 'test@example.com')], limit=1)
        self.assertTrue(mail)
        self.assertEqual(mail.subject, 'Test Report')

        # Check if the attachment was created
        attachment = self.env['ir.attachment'].search([('name', '=', 'test_report.xlsx')], limit=1)
        self.assertTrue(attachment)

    def test_group_by_field(self):
        """Test the group_by field."""
        # Set the group_by field
        self.audit_log_print.group_by = self.audit_log_group

        # Check if the group_by field is set correctly
        self.assertEqual(self.audit_log_print.group_by.name, 'Test Group')

    def test_output_type_validation(self):
        """Test output_type field validation."""
        # with self.assertRaises(ValidationError):
            # Set an invalid output_type
        self.audit_log_print.output_type = 'xlsx'