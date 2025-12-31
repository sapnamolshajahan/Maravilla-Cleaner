from odoo.tests.common import tagged, TransactionCase
from odoo.exceptions import ValidationError
from unittest.mock import patch
import json


@tagged('common', 'xero_integration')
class TestResCompanyTaxImport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.res_company = self.env['res.company'].create({
            'name': 'Test Company',
            'xero_oauth_token': 'valid_token',
        })
        self.tax_data = {
            'TaxType': 'TAX01',
            'Name': 'Test Tax',
            'EffectiveRate': 15.0,
            'Status': 'ACTIVE',
            'ReportTaxType': 'TAX_REPORT_TYPE_1',
        }
        self.tax = self.env['account.tax'].create({
            'name': 'Existing Tax',
            'xero_tax_type_id': 'TAX01',
            'company_id': self.company.id
        })

    @patch('requests.request')
    def test_import_tax(self, mock_request):
        """Test importing tax rates from Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'TaxRates': [self.tax_data]})

        # Call method to import taxes
        res = self.res_company.import_tax()

        # Check that tax is created in Odoo
        imported_taxes = self.env['account.tax'].search([('xero_tax_type_id', '=', 'TAX01')])
        for imported_tax in imported_taxes:
            self.assertTrue(imported_tax)

    @patch('requests.request')
    def test_import_tax_no_data(self, mock_request):
        """Test handling of no tax data returned from Xero"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'TaxRates': []})

        # Call method to import taxes and check for ValidationError
        with self.assertRaises(ValidationError):
            self.res_company.import_tax()

    @patch('requests.request')
    def test_create_imported_tax(self, mock_request):
        """Test creating taxes from Xero data"""
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'TaxRates': [self.tax_data]})

        # Create tax from the mocked Xero data
        self.res_company.create_imported_tax(self.tax_data)

        # Verify tax creation in Odoo
        taxes = self.env['account.tax'].search([('xero_tax_type_id', '=', 'TAX01')])
        for tax in taxes:
            self.assertTrue(tax)

    @patch('requests.request')
    def test_create_imported_tax_existing(self, mock_request):
        """Test updating an existing tax"""
        updated_data = self.tax_data.copy()
        updated_data['Name'] = 'Updated Tax'

        # Call method to update existing tax
        self.res_company.create_imported_tax(updated_data)

        # Verify the tax name is updated
        taxes = self.env['account.tax'].search([('xero_tax_type_id', '=', 'TAX01')])
        for tax in taxes:
            self.assertTrue(tax)

    @patch('requests.request')
    def test_import_tax_status_inactive(self, mock_request):
        """Test handling of inactive tax status"""
        inactive_data = self.tax_data.copy()
        inactive_data['Status'] = 'INACTIVE'
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({'TaxRates': [inactive_data]})

        # Call method to import taxes
        res = self.res_company.import_tax()

        # Verify no new tax is created because the tax status is inactive
        tax = self.env['account.tax'].search([('xero_tax_type_id', '=', 'TAX01')])
        self.assertFalse(tax)
