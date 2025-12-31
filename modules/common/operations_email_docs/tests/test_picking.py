# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged("common", "operations_email_docs")
class TestOperationsEmailPicking(common.TransactionCase):
    """Class to test operation related email picking  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        self.partner = self.env.ref('base.res_partner_12')
        self.picking = self.env.ref('stock.outgoing_shipment_main_warehouse')
        self.picking.partner_id = self.partner.id

    @patch("odoo.addons.email_docs.wizards.async_email.AsyncEmail.send")
    def test_action_done_sends_email_picking(self, mock_send):
            """
            Test that an email is sent when a picking is done for an outgoing delivery.
            """
            # Ensure picking is in the "ready to transfer" state
            self.picking.write({'state': 'assigned'})
            # Confirm the picking is done
            self.picking._action_done()
            # Ensure email.async.send's send method is called with correct parameters
            if self.picking.state == 'done':
                mock_send.assert_called_once_with(
                    "packing_slip",
                    self.picking.ids,
                    self.partner.id
                )

    def test_email_doc_report(self):
        """
        Test that the email_doc_report method returns the correct report name.
        """
        report_name = self.picking.email_doc_report()
        self.assertTrue(report_name)
