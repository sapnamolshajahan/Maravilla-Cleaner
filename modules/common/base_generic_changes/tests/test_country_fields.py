# -*- coding: utf-8 -*-
from odoo.tests import Form
from odoo.tests.common import tagged
from .common import BaseGenericChangesCommonCase


@tagged("common", "base_generic_changes")
class TestCountryFields(BaseGenericChangesCommonCase):

    def setUp(self):
        super(TestCountryFields, self).setUp()

    def test_company_tax_name(self):
        with Form(self.country) as f:
            f.company_tax_name = "ABC"
        self.assertEqual(self.country.company_tax_name, "ABC")
