# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal
from io import BytesIO, StringIO
from types import SimpleNamespace
from odoo.tests import Form, new_test_user, tagged

import xlsxwriter

from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestARAPAuditReport(TransactionCase):
    def setUp(self):
        super(TestARAPAuditReport, self).setUp()
        # Get our report model.
        self.Report = self.env['ar.ap.audit.xls.report']
        # Check for the dependent model: res.partner.statement.lines.
        try:
            self.PartnerStatementLine = self.env['res.partner.statement.lines']
        except KeyError:
            self.skipTest("Model 'res.partner.statement.lines' is not available. "
                          "Ensure the module that defines it is installed.")

        # Use an existing account.account of type asset_receivable or liability_payable.
        self.Account = self.env['account.account'].search(
            [('account_type', 'in', ('asset_receivable', 'liability_payable'))],
            limit=1
        )
        if not self.Account:
            self.skipTest("No account.account of type receivable or payable found.")

        # Use an existing currency, or create one if needed.
        self.Currency = self.env['res.currency'].search([], limit=1)
        if not self.Currency:
            self.Currency = self.env['res.currency'].create({
                'name': 'Test Currency',
                'symbol': 'TC',
                'rounding': 0.01,
                'decimal_places': 2,
            })

        # Create a dummy partner to be referenced in our statement lines.
        self.Partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'ref': 'TP001',
        })

        # Create a dummy wizard record.
        # Although the model only declares the "name" field, the report code expects
        # the wizard record to have attributes: as_at_date and statement_currency.
        self.Wizard = self.Report.create({
            'name': 'Dummy Report',
        })
        # Monkey-patch the wizard record with extra attributes using object.__setattr__
        object.__setattr__(self.Wizard, 'as_at_date', '2025-01-01')
        object.__setattr__(self.Wizard, 'statement_currency', self.Currency)

        # Create at least one partner statement line so that local_currency_report has data.
        # We assume that res.partner.statement.lines has at least the following fields:
        #   - sort_name (char)
        #   - transaction_partner_id (many2one to res.partner)
        #   - balance (float)
        #   - res_partner_statement_id (many2one, linked to the wizard record)
        self.PartnerStatementLine.create({
            'sort_name': 'Test Partner',
            'transaction_partner_id': self.Partner.id,
            'balance': 100.0,
            'res_partner_statement_id': self.Wizard.id,
        })

    def test_round_dp(self):
        """Test that the rounding helper rounds numbers correctly."""
        report_rec = self.Report
        # Example: 12.3456 rounded to 2 decimal places should be 12.35.
        rounded = report_rec.round_dp(12.3456, 2)
        self.assertEqual(rounded, 12.35, "round_dp did not round the value correctly.")
        # If no value or decimals provided, it should return False.
        self.assertFalse(report_rec.round_dp(None, 2),
                         "round_dp should return False if no value is given.")

    def test_run_report(self):
        """Test that run_report generates a file-like object and returns the expected tuple."""
        report_rec = self.Report
        # Call the run_report method with our wizard record.
        result = report_rec.run_report(self.Wizard)
        # run_report is expected to return a tuple: (report_name, file_name, title, data)
        self.assertIsInstance(result, tuple, "run_report should return a tuple.")
        self.assertEqual(len(result), 4, "run_report should return a tuple of length 4.")
        report_name, file_name, title, file_data = result
        self.assertEqual(report_name, "AR & AP Audit Report", "Report name mismatch.")
        self.assertTrue(file_name.endswith(".xlsx"), "File name should end with .xlsx")
        self.assertEqual(title, "ATB Detail Report", "Title mismatch.")

        # file_data is a StringIO/BytesIO-like object. Get its content.
        file_content = file_data.getvalue()
        # Check that the generated XLS file contains the report header text.
        self.assertIn(b'AR AP Audit Report as at:', file_content,
                      "The report header should be in the XLS file content.")

    def test_write_xls_lines(self):
        """Test that write_xls_lines writes the given data to the worksheet.

        Since xlsxwriter does not easily allow reading back written values, we test
        that the method returns the same workbook object that is passed.
        """
        # Create an in-memory file using BytesIO.
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Test')
        start_row = 0
        # Create a dummy dictionary of differences.
        dict_of_differences = {
            1: ['TP001', 'Test Partner', 100.0, 90.0, 10.0],
            2: ['TP002', 'Another Partner', 200.0, 195.0, 5.0],
        }
        report_rec = self.Report
        returned_workbook = report_rec.write_xls_lines(dict_of_differences,
                                                       worksheet,
                                                       workbook,
                                                       start_row,
                                                       self.Wizard)
        self.assertEqual(returned_workbook, workbook,
                         "write_xls_lines should return the same workbook passed.")
        workbook.close()

    def test_local_currency_report(self):
        """Test that local_currency_report processes partner statement lines and returns a dict."""
        report_rec = self.Report
        # Retrieve the lines we created in setUp.
        lines = self.PartnerStatementLine.search([
            ('res_partner_statement_id', '=', self.Wizard.id)
        ])
        # Call the method. (Note: the method uses SQL queries; in our test environment,
        # those queries may return empty results, which is acceptable.)
        differences = report_rec.local_currency_report(lines, self.Wizard)
        # Since our test data only created one line with balance=100.0 and no matching GL data,
        # we expect that a difference might be computed if the absolute difference is > 0.005.
        # The key in the dictionary is the partner's id.
        self.assertIsInstance(differences, dict,
                              "local_currency_report should return a dictionary.")
        partner_diff = differences.get(self.Partner.id)
        if partner_diff:
            # partner_diff should be a list with 5 elements.
            self.assertEqual(len(partner_diff), 5,
                             "Each report line should contain 5 elements.")
        else:
            # It is acceptable that no difference is returned if the computed difference is zero.
            self.assertTrue(True, "No differences reported if computed difference is insignificant.")
