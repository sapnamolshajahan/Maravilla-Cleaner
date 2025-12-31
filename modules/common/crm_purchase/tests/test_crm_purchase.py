# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "crm_purchase")
class TestCrmPurchase(common.TransactionCase):
    """Class to test crm and purchase  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.crm_lead = self.env.ref('crm.crm_case_1')
        self.crm_lead_2 = self.env.ref('crm.crm_case_2')
        self.purchase = self.env.ref('purchase.purchase_order_1')
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('product.product_product_6')

    def test_crm_purchase(self):
        """
         Check different action changes in crm like button functionality to open purchase order forms and compute
         functionality of field
        """
        # Check action view in purchase_order
        crm_lead_without_purchase_order = self.crm_lead.action_view_purchases()
        self.assertEqual(crm_lead_without_purchase_order.get('context')['opportunity'], self.crm_lead.id)
        self.crm_lead.get_count()  # compute functionality in purchase_count
        self.assertEqual(self.crm_lead.purchase_count, 0)
        self.crm_lead.write({
            "purchases": [[6, 0, [self.purchase.id]]],
        })
        self.crm_lead.get_count()
        self.assertEqual(self.crm_lead.purchase_count, 1)
        crm_lead_with_purchase_order = self.crm_lead.action_view_purchases()
        self.assertEqual(crm_lead_with_purchase_order['res_model'], 'purchase.order')
        self.assertEqual(crm_lead_with_purchase_order['res_id'], self.purchase.id)
        self.assertEqual(self.crm_lead.purchases.ids, crm_lead_with_purchase_order.get('domain')[0][2])
