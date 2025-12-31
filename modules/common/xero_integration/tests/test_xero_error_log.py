from odoo.tests.common import tagged, TransactionCase
import json


@tagged('common', 'xero_integration')
class TestXeroErrorLog(TransactionCase):

    def setUp(self):
        super(TestXeroErrorLog, self).setUp()
        self.error_log_model = self.env['xero.error.log']
        self.test_record = self.env['res.partner'].create({
            'name': 'Test Partner'
        })

    def test_success_log(self):
        """Test that a success log is created properly."""
        transaction_name = 'Test Success Transaction'
        self.error_log_model.success_log(self.test_record, transaction_name)

        log = self.error_log_model.search([('transaction', '=', transaction_name)], limit=1)
        self.assertTrue(log, "The success log was not created.")
        self.assertEqual(log.record_id, str(self.test_record), "The record_id in the success log is incorrect.")
        self.assertEqual(log.record_name, self.test_record.name, "The record_name in the success log is incorrect.")
        self.assertEqual(log.state, 'success', "The state in the success log is incorrect.")

    def test_error_log_with_record(self):
        """Test that an error log is created properly when a record is provided."""
        transaction_name = 'Test Error Transaction'
        error_response = json.dumps({
            "Elements": [
                {
                    "ValidationErrors": [
                        {"Message": "Test error message 1"},
                        {"Message": "Test error message 2"}
                    ]
                }
            ]
        })

        self.error_log_model.error_log(self.test_record, transaction_name, error_response)

        log = self.error_log_model.search([('transaction', '=', transaction_name)], limit=1)
        self.assertTrue(log, "The error log was not created.")
        self.assertEqual(log.record_id, str(self.test_record.id), "The record_id in the error log is incorrect.")
        self.assertEqual(log.record_name, self.test_record.name, "The record_name in the error log is incorrect.")
        self.assertEqual(log.state, 'error', "The state in the error log is incorrect.")
        self.assertEqual(
            log.xero_error_msg,
            "Test error message 1\nTest error message 2",
            "The error messages in the error log are incorrect."
        )

    def test_error_log_without_record(self):
        """Test that an error log is created properly when no record is provided."""
        transaction_name = 'Test Error Transaction Without Record'
        error_response = json.dumps({
            "Elements": [
                {
                    "ValidationErrors": [
                        {"Message": "Test error message without record"}
                    ]
                }
            ]
        })

        self.error_log_model.error_log(None, transaction_name, error_response)

        log = self.error_log_model.search([('transaction', '=', transaction_name)], limit=1)
        self.assertTrue(log, "The error log was not created.")
        self.assertFalse(log.record_id, "The record_id in the error log should be empty.")
        self.assertEqual(log.record_name, transaction_name, "The record_name in the error log is incorrect.")
        self.assertEqual(log.state, 'error', "The state in the error log is incorrect.")
        self.assertEqual(
            log.xero_error_msg,
            "Test error message without record",
            "The error messages in the error log are incorrect."
        )

    def test_error_log_invalid_json(self):
        """Test that an error is raised when an invalid JSON string is passed."""
        transaction_name = 'Test Invalid JSON Transaction'
        invalid_error_response = "Invalid JSON String"

        with self.assertRaises(json.JSONDecodeError):
            self.error_log_model.error_log(self.test_record, transaction_name, invalid_error_response)
