# -*- coding: utf-8 -*-
import logging

from io import BytesIO
from odoo.tests import common, tagged
from odoo.exceptions import UserError
import base64
from openpyxl import Workbook

_logger = logging.getLogger(__name__)

@tagged("common", "operations_import_transfers")
class TestOperationsImportTransfers(common.TransactionCase):
    """Class to test operation related stock.picking import csv workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.picking = self.env.ref('stock.incomming_shipment1')
        self.picking.picking_type_id.code = 'internal'
        self.picking.state = 'draft'
        self.product_1 = self.env.ref('product.product_product_6')
        self.product_1.write({
            'default_code': 'TP1',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
        })
        self.product_2 = self.env.ref('product.product_product_5')
        self.product_2.write({
            'default_code': 'TP2',
            'uom_id': self.env.ref('uom.product_uom_unit').id,
        })

        # Prepare an Excel file
        wb = Workbook()
        ws = wb.active
        ws.append(['Default Code', 'Quantity'])
        ws.append(['TP1', 10])
        ws.append(['TP2', 5])
        ws.append(['INVALID_CODE', 3])  # Invalid product code
        ws.append(['TP1', 'IFURN_7777NVALID_QTY'])  # Invalid quantity
        # Save the Excel file in memory
        file_stream = BytesIO()
        wb.save(file_stream)
        self.file_data = base64.b64encode(file_stream.getvalue())

    def test_action_import_transfers_valid(self):
        """Test that the wizard is opened for valid conditions."""
        result = self.picking.action_import_transfers()
        self.assertEqual(result['res_model'], 'import.transfers.csv',
                         "The result model should be 'import.transfers.csv'")
        self.assertEqual(result['type'], 'ir.actions.act_window', "The action type should be 'ir.actions.act_window'")
        self.assertEqual(result['target'], 'new', "The action target should be 'new'")

    def test_action_import_transfers_invalid_picking_type(self):
        """Test that an error is raised for non-internal picking type."""
        self.picking.picking_type_id.code = 'outgoing'
        with self.assertRaises(UserError, msg="Only for internal transfers"):
            self.picking.action_import_transfers()

    def test_action_import_transfers_invalid_state(self):
        """Test that an error is raised for non-draft picking state."""
        self.picking.state = 'done'
        with self.assertRaises(UserError, msg="Can only import when transfer is in draft state"):
            self.picking.action_import_transfers()

    def test_button_import(self):
        """Test the import of stock moves using the wizard."""
        result = self.picking.action_import_transfers()
        wizard = self.env['import.transfers.csv'].browse(result['res_id'])
        wizard.write({
            'file': self.file_data,
        })
        result = wizard.button_import()
        self.assertEqual(result['type'], 'ir.actions.act_window_close', "The action type should be 'ir.actions.act_window_close'.")
        moves = self.env['stock.move'].search([('picking_id', '=', self.picking.id)])
        self.assertEqual(len(moves), 3, "Two valid stock moves should have been created.") # incomming_shipment1 exist 1 move default code is FURN_7777
        self.assertTrue(all(move.product_id.default_code in ['TP1', 'TP2', 'FURN_7777'] for move in moves), "Only valid products should have moves.")
        self.assertTrue(all(move.product_uom_qty > 0 for move in moves), "Quantities should be greater than 0.")
