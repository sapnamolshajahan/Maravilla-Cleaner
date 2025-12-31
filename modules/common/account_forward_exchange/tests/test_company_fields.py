# -*- coding: utf-8 -*-
from odoo.tests.common import tagged, TransactionCase


@tagged("common", "account_forward_exchange")
class TestCompanyFields(TransactionCase):

    def setUp(self):
        super(TestCompanyFields, self).setUp()

    def test_fec_mode(self):
        company = self.env.company
        self.assertEqual(company.fec_mode, "ibr")  # Default should be ibr
