# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "sale_generic_changes")
class TestResPartnerSales(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Create company and enable setting
        self.company = self.env['res.company'].create({'name': 'Test Company'})
        self.company.sale_set_counts_zero = False
        # Create partners
        self.parent_partner = self.env['res.partner'].create({'name': 'Parent Partner'})
        self.child_partner = self.env['res.partner'].create({'name': 'Child Partner', 'parent_id': self.parent_partner.id})
        # Create sale orders
        self.sale_order_1 = self.env['sale.order'].create({'partner_id': self.parent_partner.id})
        self.sale_order_2 = self.env['sale.order'].create({'partner_id': self.child_partner.id})

    def test_compute_override_values_sales(self):
        # Test case when sale_set_counts_zero is False
        self.env.company = self.company
        self.company.sale_set_counts_zero = False
        self.parent_partner._compute_override_values_sales()
        self.assertEqual(self.parent_partner.sale_order_count, 2, "Parent partner should count all child sales.")
        self.assertEqual(self.child_partner.sale_order_count, 1, "Child partner should count its own sales.")
        # Test case when sale_set_counts_zero is True
        self.company.sale_set_counts_zero = True
        self.parent_partner._compute_override_values_sales()
        self.assertEqual(self.parent_partner.sale_order_count, 0, "Sale count should be zero when setting is enabled.")
