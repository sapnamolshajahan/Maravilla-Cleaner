# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "project_to_purchase")
class TestProjectPurchase(common.TransactionCase):
    """Class to test project and purchase  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.project = self.env.ref('project.project_project_1')
        self.purchase = self.env.ref('purchase.purchase_order_1')

    def test_project_purchase_action_changes(self):
        """
         Check different action changes in project like button functionality to open purchase order forms and compute
         functionality of field
        """
        # Check action view in purchase_order
        project_without_sale_order = self.project.action_view_po()
        self.assertEqual(project_without_sale_order['params'].get('title'), 'No Purchase Orders')
        self.assertEqual(project_without_sale_order['params'].get('message'), 'There are no purchase orders in this '
                                                                              'project')
        self.project._calc_purchases()  # compute functionality in purchase_orders_count and
        self.assertEqual(self.project.purchase_orders_count, 0)
        self.project.write({
            "purchase_orders": [[6, 0, [self.project.id]]],
        })
        self.project._calc_purchases()
        self.assertEqual(self.project.purchase_orders_count, 1)
        form = self.project.action_view_po()
        self.assertEqual(form['res_model'], 'purchase.order')
        self.assertEqual(form['res_id'], self.purchase.id)

    def test_purchase_project_changes(self):
        """
        Check changes of functionality in purchase
        """
        self.purchase.write({
            'account_analytic': self.project.analytic_account_id.id
        })
        self.purchase.onchange_account_analytic()
        self.assertEqual(self.project, self.purchase.project)
