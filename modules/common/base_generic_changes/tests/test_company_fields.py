# -*- coding: utf-8 -*-
from odoo.tests import Form
from odoo.tests.common import tagged
from .common import BaseGenericChangesCommonCase


@tagged("common", "base_generic_changes")
class TestCompanyFields(BaseGenericChangesCommonCase):

    def setUp(self):
        super(TestCompanyFields, self).setUp()

    def test_account_email_address(self):
        with Form(self.company) as f:
            f.account_email_address = "blah"
        self.assertEqual(self.company.account_email_address, "blah")
