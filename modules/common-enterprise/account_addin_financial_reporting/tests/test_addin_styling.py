# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields
import xlsxwriter
import io
from odoo.odoo.tests import tagged


@tagged('account_addin_financial_reporting')
class TestAddinStyling(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Style = self.env['report.xlsx.style']
        self.Styling = self.env['addin.styling']
        self.Group = self.env['addin.styling.account.group']

        # Create mock styles
        self.default_style = self.Style.create({'name': 'Default Style'})
        self.header_style = self.Style.create({'name': 'Header Style'})
        self.footer_style = self.Style.create({'name': 'Footer Style'})

        # Create styling record
        self.styling = self.Styling.create({
            'name': 'Test Styling',
            'default_text': self.default_style.id,
            'default_line_value': self.default_style.id,
            'title': self.default_style.id,
            'parameters': self.default_style.id,
            'chart': self.default_style.id,
            'column': self.default_style.id,
            'code': self.default_style.id,
            'col_width_name': 20,
            'col_width_desc': 50,
            'col_width_value': 20,
        })

        # Add group styles
        self.group_style = self.Group.create({
            'styling': self.styling.id,
            'name': 1,
            'header': self.header_style.id,
            'footer': self.footer_style.id,
        })

    def test_generate_formats(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        formats = self.styling.generate_formats('dollar', workbook)

        # Check that formats are created
        self.assertTrue(hasattr(formats, 'default_text'))
        self.assertTrue(hasattr(formats, 'default_dollar'))
        self.assertIn(1, formats.group)

        group_format = formats.group[1]
        self.assertTrue(hasattr(group_format, 'header'))
        self.assertTrue(hasattr(group_format, 'footer'))

        workbook.close()
