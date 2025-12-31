import base64
import tempfile

import xlwt

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests.common import tagged


@tagged('common', 'xero_ar_ap_migration')
class TestXeroImport(TransactionCase):

    def setUp(self):
        super(TestXeroImport, self).setUp()
        # Create accounts for testing
        self.debit_account = self.env["account.account"].sudo().create(
            {
                "name": "Test Debit Account",
                "code": "DEB001",
                "account_type": "liability_payable",
                "reconcile": True,
            })
        self.credit_account = self.env["account.account"].sudo().create(
            {
                "name": "Test Credit Account",
                "code": "CRED001",
                "account_type": "asset_receivable",
                "reconcile": True,
            })

        # Create Xero Import wizard
        self.xero_import = self.env['xero.import'].create({
            'move_type': 'receivable',
            'debit_account': self.debit_account.id,
            'credit_account': self.credit_account.id,
        })

    def create_test_file(self):
        """
        Create a temporary XLS file for testing.
        """
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Sheet1')

        # Add header
        headers = ['Invoice Date', 'Due Date', 'Invoice Number', 'Partner', 'Amount']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        # Add data rows
        rows = [
            [44562, 44569, 'INV-001', 'Test Partner', 100.0],  # Valid data
            [44563, 44570, 'INV-002', 'Test Partner', -50.0],  # Refund
        ]
        for row_no, row in enumerate(rows, start=1):
            for col_no, value in enumerate(row):
                sheet.write(row_no, col_no, value)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        workbook.save(temp_file.name)
        temp_file.seek(0)

        return base64.b64encode(temp_file.read())

    def test_button_import_file(self):
        """
        Test the file import process.
        """
        # Create a test import file
        test_file = self.create_test_file()
        self.xero_import.import_file = test_file

        # Execute the import process
        self.xero_import.button_import_file()

        # Validate results
        moves = self.env['account.move'].search([])
        self.assertEqual(len(moves), 2, "Two account moves should be created.")

        move1 = moves.filtered(lambda m: m.ref == 'INV-001')
        self.assertEqual(move1.partner_id.name, 'Test Partner', "Partner should match.")
        self.assertEqual(move1.amount_total, 100.0, "Amount should match.")

        move2 = moves.filtered(lambda m: m.ref == 'INV-002')
        self.assertEqual(move2.partner_id.name, 'Test Partner', "Partner should match.")
        self.assertEqual(move2.amount_total, -50.0, "Refund amount should match.")

    def test_invalid_file(self):
        """
        Test the behavior when an invalid file is uploaded.
        """
        self.xero_import.import_file = base64.b64encode(b"This is not a valid XLS file.")

        with self.assertRaises(ValidationError):
            self.xero_import.button_import_file()
