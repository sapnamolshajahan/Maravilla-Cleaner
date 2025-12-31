# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class BaseGenericChangesCommonCase(TransactionCase):

    def setup(self):
        super(BaseGenericChangesCommonCase, self).setup()

    @classmethod
    def setUpClass(cls):
        super(BaseGenericChangesCommonCase, cls).setUpClass()
        cls.company = cls.env.company
        cls.country = cls.env['res.country'].search([], limit=1)
