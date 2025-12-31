from odoo.tests.common import tagged, TransactionCase
from unittest.mock import patch
from odoo.exceptions import ValidationError
import json


@tagged('common', 'xero_integration')
class TestAccountPaymentExport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': 'Bank Journal',
            'type': 'bank',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'company_id': self.company.id,
        })
        self.payment = self.env['account.payment'].create({
            'amount': 100.0,
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'name': 'Test Payment',
        })

    def test_prepare_payment_export_dict(self):
        """Test the creation of payment export data"""
        payment_vals = self.payment.prepare_payment_export_dict()

        # Assert that payment export data contains expected fields
        self.assertIn('Amount', payment_vals)
        self.assertEqual(payment_vals['Amount'], 100.0)
        self.assertIn('Date', payment_vals)
        self.assertEqual(payment_vals['Date'], '2025-01-01')
        self.assertIn('Reference', payment_vals)
        self.assertEqual(payment_vals['Reference'], 'Test Payment')
        self.assertIn('Account', payment_vals)
        self.assertIn('AccountID', payment_vals['Account'])
        self.assertTrue(payment_vals['Account']['AccountID'])

    @patch('requests.request')
    def test_create_payment_in_xero(self, mock_request):
        """Test creating a payment in Xero"""
        # Mock successful Xero response
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({
            'Payments': [{'PaymentID': 'XERO123'}]
        })

        # Call create_payment_in_xero and assert payment is updated with Xero Payment ID
        self.payment.create_payment_in_xero()
        self.payment.refresh()

        # Verify the Xero Payment ID is set
        self.assertEqual(self.payment.xero_payment_id, 'XERO123')

    @patch('requests.request')
    def test_create_payment_in_xero_error_400(self, mock_request):
        """Test handling of 400 error during payment creation in Xero"""
        # Mock 400 error response from Xero
        mock_request.return_value.status_code = 400
        mock_request.return_value.text = json.dumps({
            'Elements': [{'ValidationErrors': [{'Message': 'Invalid payment data'}]}]
        })

        # Call create_payment_in_xero and expect ValidationError
        with self.assertRaises(ValidationError):
            self.payment.create_payment_in_xero()

    @patch('requests.request')
    def test_create_payment_in_xero_error_401(self, mock_request):
        """Test handling of 401 error (authentication failure) during payment creation in Xero"""
        # Mock 401 error response from Xero
        mock_request.return_value.status_code = 401
        mock_request.return_value.text = json.dumps({'Message': 'Unauthorized'})

        # Call create_payment_in_xero and expect ValidationError
        with self.assertRaises(ValidationError):
            self.payment.create_payment_in_xero()

    @patch('requests.request')
    def test_export_payment_cron(self, mock_request):
        """Test cron job for exporting payments to Xero"""
        # Mock successful Xero response
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({
            'Payments': [{'PaymentID': 'XERO123'}]
        })

        # Create another payment to test the cron job
        payment_2 = self.env['account.payment'].create({
            'amount': 200.0,
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'payment_type': 'inbound',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'name': 'Test Payment 2',
        })

        # Run the cron job to export payments
        self.payment.export_payment_cron()

        # Verify that both payments have been updated with Xero Payment IDs
        self.payment.refresh()
        self.assertEqual(self.payment.xero_payment_id, 'XERO123')

        payment_2.refresh()
        self.assertEqual(payment_2.xero_payment_id, 'XERO123')

    @patch('requests.request')
    def test_export_payment_cron_no_payments(self, mock_request):
        """Test cron job when there are no payments to export"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({
            'Payments': [{'PaymentID': 'XERO123'}]
        })

        # Create a payment with a Xero Payment ID, so it won't be exported by the cron job
        self.payment.xero_payment_id = 'XERO123'

        # Run the cron job to export payments
        self.payment.export_payment_cron()

        # Verify no new payments were exported (payment should not be modified)
        self.assertEqual(self.payment.xero_payment_id, 'XERO123')
