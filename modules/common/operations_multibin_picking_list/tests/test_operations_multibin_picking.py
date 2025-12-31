# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import tagged
from odoo.addons.stock.tests.common import TestStockCommon
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged('common', 'operations_multibin_picking_list')
class TestOperationsMultibinPicking(TestStockCommon):

    def setUp(self):
        super(TestOperationsMultibinPicking, self).setUp()
        self.stock_picking = self.env['stock.picking'].create({
            'name': 'Test Picking',
            'location_id': self.stock_location,
            'location_dest_id': self.customer_location,
            'picking_type_id': self.picking_type_out
        })

    def test_action_print_picking(self):
        """Test that action_print_picking triggers the correct report action."""
        report_ref = "operations_multibin_picking_list.standard_picking_viaduct_for_bin"
        expected_report = self.env.ref(report_ref)
        with patch('odoo.addons.operations_multibin_picking_list.models.picking.StockPickings.get_picking_report',
                   return_value=expected_report):
            report_action = self.stock_picking.action_print_picking()
            self.assertEqual(report_action['type'], 'ir.actions.report')
            self.assertEqual(report_action['report_name'], report_ref)

        _logger.info("Test action_print_picking passed successfully.")
