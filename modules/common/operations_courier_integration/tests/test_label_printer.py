import base64
import unittest
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.odoo.tests import tagged


@tagged('operations_courier_integration')
class TestCarrierLabelPrinter(TransactionCase):
    def setUp(self):
        super(TestCarrierLabelPrinter, self).setUp()
        self.printer = self.env['carrier.label.printer'].create({
            'name': 'Test Printer',
            'printer_type': 'pdf'
        })
        self.attachment = self.env['ir.attachment'].create({
            'name': 'Test PDF',
            'datas': base64.b64encode(b'testdata'),
            'mimetype': 'application/pdf'
        })

    def test_convert_pdf(self):
        data = self.printer.convert_pdf(self.attachment)
        self.assertEqual(data, b'testdata', "PDF conversion failed")

    @patch('odoo.addons.operations_courier_integration.printers.zebra.ZebraConverter.print_png',
           return_value='ZPL_DATA')
    def test_convert_zpl(self, mock_zebra):
        self.printer.printer_type = 'zpl'
        self.attachment.mimetype = 'image/png'
        data = self.printer.convert_zpl(self.attachment)
        self.assertEqual(data, b'ZPL_DATA', "ZPL conversion failed")

    @patch('odoo.addons.operations_courier_integration.printers.sato.SatoConverter.print_pdf', return_value='SBPL_DATA')
    def test_convert_sbpl(self, mock_sato):
        self.printer.printer_type = 'sbpl'
        data = self.printer.convert_sbpl(self.attachment)
        self.assertEqual(data, b'SBPL_DATA', "SBPL conversion failed")

    @patch('subprocess.call', return_value=0)
    def test_print_label_success(self, mock_subprocess):
        self.printer.print_label(b'test_label_data')
        mock_subprocess.assert_called_once()

    @patch('subprocess.call', return_value=1)
    def test_print_label_failure(self, mock_subprocess):
        with self.assertRaises(Exception):
            self.printer.print_label(b'test_label_data', raise_exceptions=True)
        mock_subprocess.assert_called_once()

if __name__ == '__main__':
    unittest.main()
