# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("common", "purchase_order_reports")
class TestPurchaseOrderReport(TransactionCase):
    def setUp(self):
        super(TestPurchaseOrderReport, self).setUp()
        self.purchase_order = self.env["purchase.order"].create({
            "partner_id": self.env.ref("base.res_partner_2").id,
            "company_id": self.env.company.id,
        })
        self.partner = self.purchase_order.partner_id
        self.partner.write({
            "purchase_report_pricing": "priced",
        })
        self.purchase_order.write({
            "state": "draft",
        })

    def test_set_priced_context(self):
        """Test _set_priced_context method."""
        context = self.purchase_order._set_priced_context(True)
        self.assertIn("purchase_order_reports.priced_email", context)
        self.assertTrue(context["purchase_order_reports.priced_email"])

    def test_review_email(self):
        """Test _review_email method."""
        self.purchase_order.company_id.purchase_report_email_review = True
        result = self.purchase_order._review_email(priced=True)
        self.assertTrue(result)

    def test_print_quotation(self):
        """Test print_quotation method."""
        action = self.purchase_order.print_quotation()
        self.assertTrue(action)
        self.assertEqual(self.purchase_order.state, "sent")

    def test_button_approve(self):
        """Test button_approve method."""
        self.purchase_order.button_approve()
        # Add assertions if button_approve has further customizations

    def test_button_print_report(self):
        """Test button_print_report method."""
        action = self.purchase_order.button_print_report()
        self.assertTrue(action)

    def test_button_send_by_email(self):
        """Test button_send_by_email method."""
        self.partner.purchase_report_pricing = "priced"
        result = self.purchase_order.button_send_by_email()
        self.assertTrue(result)

    def test_get_report_wizard(self):
        """Test get_report_wizard method."""
        wizard_action = self.purchase_order.get_report_wizard("email")
        self.assertEqual(wizard_action["res_model"], "purchase.order.report.wizard")
        self.assertIn("res_id", wizard_action)

    def test_action_rfq_send_context(self):
        """Test action_rfq_send_context method."""
        report = self.purchase_order.purchase_order_report()
        template = self.purchase_order.get_email_template(report)
        context = self.purchase_order.action_rfq_send_context(template, "en_US")
        self.assertIn("default_template_id", context)
        self.assertEqual(context["default_model"], "purchase.order")
        self.assertEqual(context["model_description"], "Request for Quotation")

    def test_action_rfq_send(self):
        """Test action_rfq_send method."""
        action = self.purchase_order.action_rfq_send()
        self.assertEqual(action["res_model"], "mail.compose.message")
        self.assertEqual(action["context"]["default_model"], "purchase.order")
