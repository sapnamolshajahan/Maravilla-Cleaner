# -*- coding: utf-8 -*-
import logging
import base64

from odoo import fields
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "operations_delivery_signature")
class TestOperationsDeliverySign(common.TransactionCase):
    """Class to test operations picking  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.stock_picking = self.env.ref('stock.outgoing_shipment_main_warehouse')

    def test_get_pod_captured(self):
        """Test that pod_captured is computed correctly."""
        self.stock_picking.signature = False
        self.assertEqual(self.stock_picking.pod_captured, 'no',
                         "POD Captured should be 'no' when signature is missing.")

        valid_signature_data = base64.b64encode(b"fake_signature_1")
        self.stock_picking.signature = valid_signature_data
        self.assertEqual(self.stock_picking.pod_captured, 'yes',
                         "POD Captured should be 'yes' when signature is present.")

    def test_onchange_sign_by(self):
        """Test that sign_date is updated when sign_by is set."""
        self.stock_picking.sign_by = "John Doe"
        self.stock_picking.onchange_sign_by()
        today_date = fields.Date.context_today(self.stock_picking)
        self.assertEqual(self.stock_picking.sign_date, today_date,
                         "Sign Date should be set to today's date when Sign By is updated.")

    def test_write_signature(self):
        """Test the write method when updating the signature."""
        valid_signature_data = base64.b64encode(b"fake_signature_2")
        self.stock_picking.write({'signature': valid_signature_data})
        self.assertEqual(self.stock_picking.signature, valid_signature_data,
                         "Signature field should be updated correctly.")
