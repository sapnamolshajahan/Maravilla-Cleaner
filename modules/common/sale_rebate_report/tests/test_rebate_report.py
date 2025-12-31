# -*- coding: utf-8 -*-
from datetime import date
import base64
from unittest.mock import patch
from odoo.tests import Form, new_test_user, tagged

import xlsxwriter

from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install', 'sale_rebate_report')
class TestRebateReport(TransactionCase):

    def setUp(self):
        super(TestRebateReport, self).setUp()
        self.RebateReport = self.env['rebate.report']
        self.XlsExport = self.env['rebate.report.xls_export_options']
        # Create a test partner that will be used for the report.
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'ref': 'TP001',
        })

    def test_encode_report_data(self):
        # Prepare dummy report data (a list of dictionaries with the expected keys).
        dummy_data = [{
            'parent_reference': 'TP001',
            'parent_name': 'Test Partner',
            'branch_reference': 'B001',
            'branch_name': 'Branch One',
            'product_category': 'Cat1',
            'product_code': 'P001',
            'product_description': 'Product One',
            'quantity': 10,
            'list_price': 100.0,
            'discount': 5,
            'net_price': 95.0,
            'extended_net_price': 950.0,
            'period': 'Jan-25',
            'invoice_number': 'INV001',
            'rebate_flag': True,
            'client_order_ref': 'ORD001',
        }]
        # Create a temporary rebate.report record.
        report = self.RebateReport.create({
            'partner_id': self.partner.id,
            'date_from': date(2025, 1, 1),
            'date_to': date(2025, 1, 31),
        })
        output = report._RebateReport__encode_report_data(dummy_data)
        # output is a base64 string; decode it.
        decoded = base64.b64decode(output)
        # Check that the report_name was updated (the method sets the file name based on the date).
        self.assertTrue(report.report_name.endswith('.xlsx'))
        # Check that the decoded XLS content is not empty.
        self.assertTrue(len(decoded) > 0)

    def test_check_report(self):
        # Create a rebate.report record with required fields.
        report = self.RebateReport.create({
            'partner_id': self.partner.id,
            'date_from': date(2025, 1, 1),
            'date_to': date(2025, 1, 31),
        })

        # Override _generate_report_datas to return dummy data so that check_report can run.
        def dummy_generate_report_datas(self):
            return [{
                'parent_reference': 'TP001',
                'parent_name': 'Test Partner',
                'branch_reference': 'B001',
                'branch_name': 'Branch One',
                'product_category': 'Cat1',
                'product_code': 'P001',
                'product_description': 'Product One',
                'quantity': 10,
                'list_price': 100.0,
                'discount': 5,
                'net_price': 95.0,
                'extended_net_price': 950.0,
                'period': 'Jan-25',
                'invoice_number': 'INV001',
                'rebate_flag': True,
                'client_order_ref': 'ORD001',
            }]

        with patch.object(report.__class__, '_generate_report_datas', dummy_generate_report_datas):
            action = report.check_report()
        # Verify the returned action dictionary.
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('res_model'), 'rebate.report.xls_export_options')
        export_record = self.XlsExport.browse(action.get('res_id'))
        self.assertTrue(export_record.export_xls, "Export file should not be empty.")

    def test_generate_report_datas(self):
        report = self.RebateReport.create({
            'partner_id': self.partner.id,
            'date_from': date(2025, 1, 1),
            'date_to': date(2025, 1, 31),
        })

        # Define dummy helper methods.
        def dummy_get_invoice_lines(self, partner_ids):
            return [(self.partner_id.id, 1001)]

        def dummy_get_all_partners(self, partner_id):
            return []

        def dummy_generate_report_lines(self, datas, parent_partner_id):
            # Return a list with a dummy report line.
            return [{
                'parent_reference': 'TP001',
                'parent_name': 'Test Partner',
                'branch_reference': None,
                'branch_name': None,
                'product_category': 'Cat1',
                'product_code': 'P001',
                'product_description': 'Product One',
                'quantity': 10,
                'list_price': 100.0,
                'discount': 5,
                'net_price': 95.0,
                'extended_net_price': 950.0,
                'period': 'Jan-25',
                'invoice_number': 'INV001',
                'rebate_flag': True,
                'client_order_ref': 'ORD001',
            }]

        with patch.object(report.__class__, '_RebateReport__get_invoice_lines', dummy_get_invoice_lines), \
                patch.object(report.__class__, '_RebateReport__get_all_partners', dummy_get_all_partners), \
                patch.object(report.__class__, '_RebateReport__generate_report_lines', dummy_generate_report_lines):
            report_datas = report._generate_report_datas()

        # Verify that the returned datas is a list containing our dummy report line.
        self.assertIsInstance(report_datas, list)
        self.assertEqual(len(report_datas), 1)
        report_line = report_datas[0]
        # Verify that all expected keys are present in the report line.
        expected_keys = [
            'parent_reference', 'parent_name', 'branch_reference', 'branch_name',
            'product_category', 'product_code', 'product_description', 'quantity',
            'list_price', 'discount', 'net_price', 'extended_net_price', 'period',
            'invoice_number', 'rebate_flag', 'client_order_ref'
        ]
        for key in expected_keys:
            self.assertIn(key, report_line, f"Missing key: {key}")
