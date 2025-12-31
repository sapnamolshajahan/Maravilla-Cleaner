# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


@tagged("common", "purchase_order_line_import_csv")
class TestPurchaseOrderLineImportCSV(common.TransactionCase):
    """Class to test project and purchase import csv workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.purchase_order = self.env["purchase.order"].create({
            "partner_id": self.env.ref('base.res_partner_2').id,
            "state": "draft"
        })
        self.purchase_order_line1 = self.env["purchase.order.line"].create({
            "order_id": self.purchase_order.id,
            "product_id": self.env.ref('product.product_product_6').id,
            "product_qty": 2,
            "price_unit": 50,
        })

        self.purchase_order_line2 = self.env["purchase.order.line"].create({
            "order_id": self.purchase_order.id,
            "product_id":self.env.ref('product.product_product_7').id,
            "product_qty": 1,
            "price_unit": 100,
        })

    def test_action_import_purchase_order_lines_success(self):
        """Test successful triggering of the import wizard for purchase order lines."""
        result = self.purchase_order.action_import_purchase_order_lines()
        self.assertEqual(result["res_model"], "purchase.order.line.import", "Incorrect model for the wizard.")
        self.assertEqual(result["target"], "new", "The target should be 'new'.")
        self.assertEqual(result["type"], "ir.actions.act_window",
                         "The action type should be 'ir.actions.act_window'.")

    def test_action_import_purchase_order_lines_failure(self):
        """Test failure when triggering the import wizard for non-draft purchase orders."""
        self.purchase_order.state = "sent"

        with self.assertRaises(UserError) as e:
            self.purchase_order.action_import_purchase_order_lines()

        self.assertEqual(
            str(e.exception),
            "Purchase Line import only available for Draft state Purchase Orders",
            "Incorrect error message for non-draft state."
        )

    def test_action_set_purchase_order_value_success(self):
        """Test successful triggering of the purchase order value wizard."""
        self.purchase_order._amount_all()
        result = self.purchase_order.action_set_purchase_order_value()
        self.assertEqual(result["res_model"], "purchase.purchase_order_value", "Incorrect model for the wizard.")
        self.assertEqual(result["target"], "new", "The target should be 'new'.")
        self.assertEqual(result["type"], "ir.actions.act_window",
                         "The action type should be 'ir.actions.act_window'.")
        wizard = self.env["purchase.purchase_order_value"].browse(result["res_id"])
        self.assertEqual(wizard.value, self.purchase_order.amount_untaxed,
                         "Wizard value does not match PO untaxed amount.")

    def test_action_set_purchase_order_value_failure(self):
        """Test failure when triggering the purchase order value wizard for non-draft state."""
        self.purchase_order.state = "purchase"

        with self.assertRaises(UserError) as e:
            self.purchase_order.action_set_purchase_order_value()

        self.assertEqual(
            str(e.exception),
            "You can only set the Purchase Order value when it's state is draft. ",
            "Incorrect error message for non-draft state."
        )

    def test_button_update_purchase_order_value(self):
        # Ensure initial untaxed amount is calculated correctly
        self.purchase_order._amount_all()
        initial_untaxed = self.purchase_order.amount_untaxed
        self.assertEqual(initial_untaxed, 200.0, "Initial untaxed amount should be 200.0")
        # Create the wizard and apply a new untaxed value
        wizard = self.env["purchase.purchase_order_value"].create({
            "purchase": self.purchase_order.id,
            "value": 300.0,  # New untaxed value
        })
        wizard.button_update_purchase_order_value()
        # Recalculate untaxed amount after the update
        self.purchase_order._amount_all()
        updated_untaxed = self.purchase_order.amount_untaxed
        self.assertEqual(updated_untaxed, 300.0, "Updated untaxed amount should be 300.0")
        # Validate updated line prices
        line1 = self.purchase_order_line1
        line2 = self.purchase_order_line2
        # Check line prices are updated proportionally
        self.assertAlmostEqual(line1.price_unit, 75.0, places=2, msg="Line 1 price_unit should be 75.0")
        self.assertAlmostEqual(line2.price_unit, 150.0, places=2, msg="Line 2 price_unit should be 150.0")
