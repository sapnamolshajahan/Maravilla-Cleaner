# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from odoo.exceptions import UserError
from odoo import fields


_logger = logging.getLogger(__name__)


@tagged("common", "audit_logging")
class TestAuditLogging(common.TransactionCase):
    def setUp(self):
        super(TestAuditLogging, self).setUp()

        # Create test models and records for logging
        self.partner_model = self.env['res.partner']
        self.partner = self.partner_model.create({
            'name': 'Audit Partner',
            'email': 'audit.partner@example.com'
        })
        self.audit_model = self.env['audit.logging']

    def test_create_with_log(self):
        """Test creation of a record with audit logging"""
        # Create a new record and log
        values = {'name': 'Audit Partner', 'email': 'audit.partner@example.com'}
        # partner = self.partner_model.create(values)
        self.env['audit.logging']._log_operation(
            'create',
            self.partner,
            {'name': 'Audit Partner', 'email': 'audit.partner@example.com'}
        )
        # Fetch the audit log

        audit_logs = self.audit_model.search([('record_id', '=', self.partner.id), ('method', '=', 'create'),('field','=','Name')])
        self.assertTrue(audit_logs, "Audit log not created for record creation.")
        self.assertEqual(audit_logs[0].new_value, str(values['name']), "New value in audit log does not match.")

    def test_write_with_log(self):
        """Test update operation with audit logging"""
        # Update the record
        self.env['audit.logging']._log_operation(
            'update',
            self.partner,
            {'email': 'updated.partner@example.com'}
        )
        # Fetch the audit log
        audit_logs = self.audit_model.search([('record_id', '=', self.partner.id), ('method', '=', 'update')])
        self.audit_logs = audit_logs
        self.assertTrue(audit_logs, "Audit log not created for record update.")
        self.assertIn('updated.partner@example.com', audit_logs.mapped('new_value'),
                      "Updated value not found in audit log.")

    def test_unlink_with_log(self):
        """Test deletion operation with audit logging"""
        # Attempt to delete the record
        self.env['audit.logging']._log_operation(
            'create',
            self.partner,
            {'name': 'Audit Partner 2', 'email': 'audit2.partner@example.com'}
        )
        audit_logs = self.audit_model.search([('record_id', '=', self.partner.id), ('method', '=', 'create')])
        with self.assertRaises(UserError):
            audit_logs.unlink()

        # Ensure no audit record is deleted
        audit_logs = self.audit_model.search([])
        self.assertTrue(audit_logs, "Audit log should not be removable.")

    def test_field_change_log(self):
        """Test logging of specific field changes"""
        #self.partner.write({'name': 'Updated Name'})
        self.env['audit.logging']._log_operation(
            'update',
            self.partner,
            {'name': 'Updated Name'}
        )

        # Fetch the audit log for the name field
        audit_logs = self.audit_model.search([('record_id', '=', self.partner.id), ('field', '=', 'Name')])
        self.assertTrue(audit_logs, "Audit log for field 'Name' not created.")
        self.assertEqual(audit_logs[0].new_value, 'Updated Name', "New value in the log is incorrect.")

    # def test_many2one_logging(self):
    #     """Test logging of Many2one fields"""
    #     company = self.env['res.company'].create({'name': 'Test Company'})
    #     self.partner.write({'company_id': company.id})
    #
    #     # Fetch the audit log for the company_id field
    #     audit_logs = self.audit_model.search([('record_id', '=', self.partner.id), ('field', '=', 'Company')])
    #     self.assertTrue(audit_logs, "Audit log for 'company_id' not created.")
    #     self.assertEqual(audit_logs[0].new_value, company.display_name, "New value for 'company_id' is incorrect.")
