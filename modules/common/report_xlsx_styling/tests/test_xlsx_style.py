# -*- coding: utf-8 -*-
import logging
from xlsxwriter import Workbook
from io import BytesIO
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('common', 'report_xlsx_styling')
class TestXlsxStyle(TransactionCase):
    def setUp(self):
        super(TestXlsxStyle, self).setUp()
        self.font_style = self.env["report.xlsx.style.font"].create({"name": "Arial"})

        # Create an XlsxStyle record
        self.xlsx_style = self.env["report.xlsx.style"].create({
            "name": "Test Style",
            "font_name": self.font_style.id,
            "font_size": 12,
            "bold": True,
            "italic": False,
            "underline": False,
            "border_full": True,
            "border_full_style": "1",
            "h_align": "left",
            "v_align": "top",
            "foreground": "#FF0000",
            "background": "#00FF00"
        })

    def test_xlsx_style_creation(self):
        """ Test that the XlsxStyle record is created correctly """
        self.assertTrue(self.xlsx_style, "XlsxStyle record was not created")
        self.assertEqual(self.xlsx_style.font_name.name, "Arial", "Font name is incorrect")
        self.assertEqual(self.xlsx_style.font_size, 12, "Font size mismatch")
        self.assertTrue(self.xlsx_style.bold, "Bold property should be True")

    def test_build_format(self):
        """ Test the build_format method """
        output = BytesIO()
        workbook = Workbook(output)
        xls_format = self.xlsx_style.build_format(workbook)
        _logger.info("xls_format %s", xls_format)
        workbook.close()

    def tearDown(self):
        """ Cleanup after tests """
        self.xlsx_style.unlink()
        self.font_style.unlink()
