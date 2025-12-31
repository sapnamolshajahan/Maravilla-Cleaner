# -*- coding: utf-8 -*-
import logging
from odoo.tests import tagged, TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'operations_picking_list_reports')
class TestStockPickingReport(TransactionCase):
    """
    Test case for stock picking list reports.
    """

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.stock_picking = self.env['stock.picking'].create({
            'name': 'Test Picking',
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })

    def test_get_picking_report(self):
        """Test if get_picking_report returns the correct report reference."""
        report = self.stock_picking.get_picking_report()
        self.assertTrue(report, "Report reference should not be empty")
        self.assertEqual(report.id, self.env.ref("operations_picking_list_reports.standard_picking_viaduct").id,
                         "Incorrect report reference returned")

    def test_action_print_picking(self):
        """Test the action_print_picking method to ensure correct report action."""
        report = self.env.ref("operations_picking_list_reports.standard_picking_viaduct")

        action = self.stock_picking.action_print_picking()

        self.assertEqual(action["type"], "ir.actions.report", "Incorrect action type")
        self.assertEqual(action["report_name"], report.report_name, "Incorrect report name")
        self.assertEqual(action["report_type"], report.report_type, "Incorrect report type")
        self.assertEqual(action["report_file"], report.report_file, "Incorrect report file")
        self.assertEqual(action["name"], report.name, "Incorrect report display name")
        self.assertEqual(action["context"]["active_ids"], self.stock_picking.ids, "Context active IDs mismatch")

    def test_get_picking_list_extra_report_data(self):
        """Test if _get_picking_list_extra_report_data returns an empty dictionary."""
        data = self.stock_picking._get_picking_list_extra_report_data()
        self.assertIsInstance(data, dict, "Report data should be a dictionary")
        self.assertEqual(data, {}, "Report data should be empty by default")
