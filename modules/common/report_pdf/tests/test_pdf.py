# -*- coding: utf-8 -*-
import base64
import os
from odoo.tests.common import TransactionCase, tagged
from fpdf import FPDF

@tagged('common', 'report_pdf')
class TestPDFCreate(TransactionCase):

    def setUp(self):
        super(TestPDFCreate, self).setUp()
        self.pdf_model = self.env["pdf.create"]

    def test_add_standard_heading(self):
        """Test that the add_standard_heading method adds the correct heading"""
        pdf = FPDF()
        pdf.add_page()
        report_name = "Test Report"

        self.pdf_model.add_standard_heading(pdf, report_name)

        pdf_file_path = "/tmp/test_report.pdf"
        pdf.output(pdf_file_path)

        with open(pdf_file_path, "rb") as f:
            pdf_content = f.read()

        self.assertTrue(pdf_content, "PDF content should not be empty")

    def test_add_column_headings(self):
        """Test that add_column_headings correctly formats column headings"""
        pdf = FPDF()
        pdf.add_page()
        heading = ["Column 1", "Column 2", "Column 3"]
        value_set = [["Data 1", "Data 2", "Data 3"]]
        use_heading = True
        heading_alignment = ["L", "C", "R"]

        pdf, num_columns, col_vals, max_length = self.pdf_model.add_column_headings(
            pdf, heading, value_set, use_heading, heading_alignment
        )

        self.assertEqual(num_columns, 3, "Number of columns should be 3")
        self.assertEqual(len(col_vals), 3, "Column values should match heading count")
        self.assertTrue(isinstance(col_vals, dict), "Column values should be a dictionary")

        pdf_file_path = "/tmp/test_column_headings.pdf"
        pdf.output(pdf_file_path)
        self.assertTrue(os.path.exists(pdf_file_path), "PDF should be saved in /tmp")

    def test_create_raw_pdf(self):
        """Test that create_raw_pdf generates a valid PDF"""
        report_name = "Test Report"
        heading = ["ID", "Name", "Amount"]
        row_data = [
            [1, "John Doe", 100.50],
            [2, "Jane Smith", 250.75]
        ]
        heading_alignment = ["L", "R"]

        pdf_content = self.pdf_model.create_raw_pdf(report_name, heading, row_data, use_heading=True, heading_alignment=heading_alignment)

        self.assertTrue(pdf_content, "Generated PDF content should not be empty")

        pdf_file_path = "/tmp/test_raw_pdf.pdf"
        with open(pdf_file_path, "wb") as f:
            f.write(pdf_content)
        self.assertTrue(os.path.exists(pdf_file_path), "PDF should be saved in /tmp")

    def test_create_pdf(self):
        """Test that create_pdf returns a base64 encoded PDF"""
        report_name = "Encoded PDF Report"
        heading = ["Field1", "Field2"]
        row_data = [[123, "Sample Data"]]

        heading_alignment = ["L", "R"]

        encoded_pdf = self.pdf_model.create_pdf(report_name, heading, row_data, use_heading=True,
                                                heading_alignment=heading_alignment)

        self.assertTrue(encoded_pdf, "Encoded PDF should not be empty")
        self.assertTrue(isinstance(encoded_pdf, bytes), "Encoded PDF should be in bytes")
        self.assertTrue(base64.b64decode(encoded_pdf), "Encoded PDF should be valid base64 data")
