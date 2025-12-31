# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from odoo import fields

_logger = logging.getLogger(__name__)

@tagged("common", "operations_sale_move_report")
class TestOperationsSaleMoveReport(common.TransactionCase):
    """Class to test operations sales move report workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.warehouse = self.env["stock.warehouse"].create({
            "name": "Test Warehouse",
            "company_id": self.company.id
        })
        self.product = self.env["product.product"].create({
            "name": "Test Product",
            "type": "consu",
        })
        self.internal_location = self.env["stock.location"].create({
            "name": "Internal Location",
            "usage": "internal",
            "company_id": self.company.id
        })
        self.customer_location = self.env["stock.location"].create({
            "name": "Customer Location",
            "usage": "customer",
            "company_id": self.company.id
        })

    def create_stock_move(self, product_qty, location_from, location_to):
        """Helper method to create stock moves"""
        return self.env["stock.move"].create({
            "name": "Test Move",
            "company_id": self.company.id,
            "product_id": self.product.id,
            "location_id": location_from.id,
            "location_dest_id": location_to.id,
            'product_uom_qty': product_qty,
            "state": "done",
            "date": fields.Datetime.now(),
        })

    def test_report_data_generation(self):
        """Test case to check if report generates data"""
        self.create_stock_move(10, self.internal_location, self.internal_location)
        self.create_stock_move(5, self.internal_location, self.customer_location)
        # Refresh the SQL view
        self.env.invalidate_all()
        report_records = self.env["sale.move.report"].search([])
        self.assertTrue(report_records, "No data found in sale.move.report")

    def test_quantity_calculation(self):
        """Test case to verify the quantity calculation"""
        self.create_stock_move(10, self.internal_location, self.internal_location)
        self.create_stock_move(5, self.internal_location, self.customer_location)
        self.env.invalidate_all()
        report_records = self.env["sale.move.report"].search([
            ("product_id", "=", self.product.id),
        ])
        total_quantity = sum(report_records.mapped("quantity"))
        self.assertEqual(total_quantity, 15, f"Expected quantity 15, got {total_quantity}")

    def test_warehouse_association(self):
        """Test that report data belongs to the correct warehouse"""
        self.create_stock_move(10, self.internal_location, self.internal_location)
        self.env.invalidate_all()
        report_record = self.env["sale.move.report"].search([("warehouse_id", "=", self.warehouse.id)])
        self.assertTrue(all(r.warehouse_id == self.warehouse for r in report_record),
                        "Incorrect warehouse in report data")

    def test_data_grouping(self):
        """Test that multiple stock moves aggregate correctly"""
        self.create_stock_move(3, self.internal_location, self.internal_location)
        self.create_stock_move(7, self.internal_location, self.internal_location)
        self.env.invalidate_all()
        report_record = self.env["sale.move.report"].search([("product_id", "=", self.product.id)])
        total_quantity = sum(report_record.mapped("quantity"))
        self.assertEqual(total_quantity, 10, f"Expected quantity 10, got {total_quantity}")

    def test_no_unposted_moves(self):
        """Ensure that only posted moves are included in the report"""
        self.create_stock_move(10, self.internal_location, self.internal_location)
        # Create a draft (unposted) move
        self.env["stock.move"].create({
            "name": "Test Move 2",
            "company_id": self.company.id,
            "product_id": self.product.id,
            "location_id": self.internal_location.id,
            "location_dest_id": self.internal_location.id,
            "product_uom_qty": 5,
            "state": "draft",
            "date": fields.Datetime.now(),
        })
        self.env.invalidate_all()
        report_record = self.env["sale.move.report"].search([("product_id", "=", self.product.id)])
        total_quantity = sum(report_record.mapped("quantity"))
        self.assertEqual(total_quantity, 10, f"Expected quantity 10, got {total_quantity}")
