# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)
@tagged("common", "sale_order_reports")
class TestSaleOrder(TransactionCase):
    def setUp(self):
        super(TestSaleOrder, self).setUp()

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
                'price_unit': 50.0,
            })],
        })

        self.template = self.env.ref("sale_order_reports.email_template_proforma")

    def test_get_sale_report(self):
        """Test the get_sale_report method."""
        report = self.sale_order.get_sale_report()
        self.assertTrue(report, "Failed to retrieve the sale report.")
        self.assertEqual(report.report_name, 'sale_order_reports.generic_sale_viaduct', "Incorrect report name.")

    def test_button_print_report(self):
        """Test the button_print_report method."""
        action = self.sale_order.button_print_report()
        self.assertEqual(action['type'], 'ir.actions.report', "Incorrect action type for button_print_report.")
        self.assertEqual(action['report_name'], 'sale_order_reports.generic_sale_viaduct', "Incorrect report name.")
        self.assertIn(self.sale_order.id, action['context']['active_ids'], "Sale order ID missing in context.")

    def test_get_printed_report_name(self):
        """Test the get_printed_report_name method."""
        expected_name_quote = f"Quotation - {self.sale_order.name.replace('/', '-')}"
        expected_name_sale = f"Sale - {self.sale_order.name.replace('/', '-')}"
        self.assertEqual(self.sale_order.get_printed_report_name(), expected_name_quote,
                         "Incorrect printed Quotation report name.")
        self.sale_order.action_confirm()
        print("self.sale_order.get_printed_report_name()", self.sale_order.get_printed_report_name())
        if self.sale_order.state in ("sale", "done"):
            self.assertEqual(self.sale_order.get_printed_report_name(), expected_name_sale, "Incorrect printed Sale Order report name.")

    def test_action_quotation_send(self):
        """Test the action_quotation_send method."""
        context = {'proforma': True}
        self.sale_order = self.sale_order.with_context(**context)

        action = self.sale_order.action_quotation_send()
        self.assertEqual(action['res_model'], 'mail.compose.message', "Incorrect res_model for action_quotation_send.")
        self.assertEqual(action['context']['proforma'], True, "Proforma context not set correctly.")
        self.assertTrue('default_template_id' in action['context'], "Default template ID missing in context.")
        self.assertEqual(action['context']['default_model'], 'sale.order', "Incorrect default model in context.")

    def test_find_mail_template(self):
        """Test the _find_mail_template method."""
        context = {'proforma': True}
        self.sale_order = self.sale_order.with_context(**context)
        template = self.sale_order._find_mail_template()
        self.assertEqual(template, self.template, "Incorrect mail template returned for proforma context.")
