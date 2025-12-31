from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch
import json


@tagged('common', 'xero_integration')
class TestTaxModel(TransactionCase):

    def setUp(self):
        super(TestTaxModel, self).setUp()
        self.tax_model = self.env['account.tax']
        self.xero_error_log = self.env['xero.error.log']
        self.company = self.env.company

        # Setup mock company data for Xero integration
        self.company.update({
            'xero_country_name': 'United Kingdom',
            'xero_oauth_token': 'mock_token'
        })

        # Create a test tax
        self.test_tax = self.tax_model.create({
            'name': 'Test Tax',
            'amount': 15.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'CanApplyToRevenue': True,
        })

    @patch('odoo.addons.xero_integration.models.tax.requests.request')
    def test_create_main_tax_in_xero_success(self, mock_request):
        """Test successful tax creation in Xero."""
        mock_response = {
            "TaxRates": [
                {
                    "TaxType": "TEST_TAX_TYPE",
                    "ReportTaxType": "OUTPUT"
                }
            ]
        }
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps(mock_response)

        self.test_tax.create_main_tax_in_xero(self.test_tax, self.company)

        self.assertEqual(self.test_tax.xero_tax_type_id, "TEST_TAX_TYPE", "TaxType was not updated correctly.")
        self.assertEqual(self.test_tax.xero_record_taxtype, "OUTPUT", "ReportTaxType was not updated correctly.")

    @patch('odoo.addons.xero_integration.models.tax.requests.request')
    def test_create_main_tax_in_xero_error(self, mock_request):
        """Test handling of a 400 error during tax creation in Xero."""
        mock_error_response = {
            "Elements": [
                {
                    "ValidationErrors": [
                        {"Message": "Invalid tax rate."}
                    ]
                }
            ]
        }
        mock_request.return_value.status_code = 400
        mock_request.return_value.text = json.dumps(mock_error_response)

        with self.assertRaises(ValidationError, msg="Expected ValidationError was not raised."):
            self.test_tax.create_main_tax_in_xero(self.test_tax, self.company)

        log = self.xero_error_log.search([('transaction', '=', 'Tax Export')], limit=1)
        self.assertTrue(log, "Error log was not created.")
        self.assertEqual(log.xero_error_msg, "Invalid tax rate.", "Error message was not logged correctly.")

    @patch('odoo.addons.xero_integration.models.tax.requests.request')
    def test_create_main_tax_in_xero_timeout(self, mock_request):
        """Test handling of a 401 error during tax creation in Xero."""
        mock_request.return_value.status_code = 401

        with self.assertRaises(ValidationError, msg="Expected ValidationError for timeout was not raised."):
            self.test_tax.create_main_tax_in_xero(self.test_tax, self.company)

    def test_prepare_tax_export_dict(self):
        """Test preparation of the tax export dictionary."""
        export_dict = self.test_tax.prepare_tax_export_dict()
        expected_dict = {
            "Name": "Test Tax",
            "TaxComponents": [
                {
                    "Name": "Test Tax",
                    "Rate": 15.0,
                    "IsCompound": "false",
                    "IsNonRecoverable": "false"
                }
            ],
            "CanApplyToEquity": "false",
            "CanApplyToLiabilities": "false",
            "CanApplyToRevenue": "true",
            "CanApplyToExpenses": "false",
            "CanApplyToAssets": "false",
        }
        self.assertDictEqual(export_dict, expected_dict, "Tax export dictionary is incorrect.")

    @patch('odoo.addons.xero_integration.models.tax.requests.request')
    def test_create_tax_in_xero(self, mock_request):
        """Test creation of tax in Xero through `create_tax_in_xero`."""
        mock_response = {
            "TaxRates": [
                {
                    "TaxType": "TEST_TAX_TYPE",
                    "ReportTaxType": "OUTPUT"
                }
            ]
        }
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps(mock_response)

        result = self.test_tax.create_tax_in_xero()
        self.assertTrue(result, "Tax creation in Xero did not return the expected result.")

        log = self.xero_error_log.search([('transaction', '=', 'Tax Export')], limit=1)
        self.assertTrue(log, "Success log was not created.")
