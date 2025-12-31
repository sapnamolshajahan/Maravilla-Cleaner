# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

@tagged("common", "sale_rebate_flag")
class TestSaleOrderRebate(TransactionCase):

    def setUp(self):
        super(TestSaleOrderRebate, self).setUp()
        self.partner_with_rebate = self.env['res.partner'].create({
            'name': 'Partner With Rebate',
            'is_eligible_for_rebates': True,
        })

        self.partner_without_rebate = self.env['res.partner'].create({
            'name': 'Partner Without Rebate',
            'is_eligible_for_rebates': False,
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_with_rebate.id,
        })

    def test_onchange_partner_with_rebate(self):
        """Test that has_rebate is True when partner is eligible for rebates."""
        self.sale_order.partner_id = self.partner_with_rebate
        self.sale_order.onchange_partner_id()
        self.assertTrue(
            self.sale_order.has_rebate,
            "The sale order's 'has_rebate' should be True when the partner is eligible for rebates."
        )

    def test_onchange_partner_without_rebate(self):
        """Test that has_rebate is False when partner is not eligible for rebates."""
        self.sale_order.partner_id = self.partner_without_rebate
        self.sale_order.onchange_partner_id()
        self.assertFalse(
            self.sale_order.has_rebate,
            "The sale order's 'has_rebate' should be False when the partner is not eligible for rebates."
        )

    def test_onchange_partner_no_partner(self):
        """Test that has_rebate is False when no partner is selected."""
        self.sale_order.partner_id = False
        self.sale_order.onchange_partner_id()
        self.assertFalse(
            self.sale_order.has_rebate,
            "The sale order's 'has_rebate' should be False when no partner is selected."
        )