# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from unittest.mock import patch

_logger = logging.getLogger(__name__)


@tagged("common", "operations_email_docs")
class TestOperationsEmailSalr(common.TransactionCase):
    """Class to test operation related email sale  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        self.partner = self.env.ref('base.res_partner_12')
        self.sale_order = self.env.ref('sale.sale_order_1')
        self.sale_order.partner_id = self.partner.id

    @patch("odoo.addons.email_docs.wizards.async_email.AsyncEmail.send")
    def test_action_done_sends_email_sale(self, mock_send):
            """
            Test that an email is sent when a picking is done for an outgoing delivery.
            """
            # Ensure picking is in the "ready to transfer" state
            self.sale_order.action_confirm()
            mock_send.assert_called_once_with(
                "sale_order",
                self.sale_order.ids,
                self.partner.id
            )

    def test_email_doc_report(self):
            """
            Test that the email_doc_report method returns the correct report name.
            """
            report_name =  self.sale_order.email_doc_report()
            self.assertTrue(report_name)
