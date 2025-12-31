# -*- coding: utf-8 -*-
import logging
from odoo.tests import tagged, TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestStockPickingReport(TransactionCase):
    """
    Test case for stock picking reports.
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

    def test_get_delivery_report(self):
        """Test if get_delivery_report returns the correct report action."""
        report = self.stock_picking.get_delivery_report()
        self.assertTrue(report, "Report action should not be empty")
        self.assertEqual(report.id, self.env.ref("operations_packing_slip_reports.standard_packing_viaduct").id,
                         "Incorrect report reference returned")

    def test_do_print_delivery(self):
        """Test the do_print_delivery method to verify report action dictionary."""
        # Get the actual report reference
        mock_report = self.env.ref("operations_packing_slip_reports.standard_packing_viaduct")

        action = self.stock_picking.do_print_delivery()

        self.assertEqual(action["type"], "ir.actions.report", "Incorrect action type")
        self.assertEqual(action["report_name"], mock_report.report_name, "Incorrect report name")
        self.assertEqual(action["report_type"], mock_report.report_type, "Incorrect report type")
        self.assertEqual(action["report_file"], mock_report.report_file, "Incorrect report file")
        self.assertEqual(action["name"], mock_report.name, "Incorrect report display name")
        self.assertIn("active_ids", action["context"], "Active IDs missing from context")
        self.assertEqual(action["context"]["active_ids"], self.stock_picking.ids, "Context active IDs mismatch")
