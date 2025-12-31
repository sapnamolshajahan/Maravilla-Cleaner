# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.tests import Form, TransactionCase


class AccountForwardExchangeSPC(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(AccountForwardExchangeSPC, cls).setUpClass()

    @classmethod
    def do_config(cls, config):
        config['enable-currencies'] = 'NZD'
        config['multi-currency'] = True
        config['rectify-currency-rates'] = {'USD': 1.0, 'EUR': 0.84, 'NZD': 1.53}
        return super(AccountForwardExchangeSPC, cls).do_config(config)

    def setUp(self):
        super(AccountForwardExchangeSPC, self).setUp()

        self.fec_model = self.env['account.forward.exchange']
        self.currency_nzd = self.env.ref('base.NZD')
        self.account = self.env.ref("account_forward_exchange.test_account_account")
        self.partner = self.env.ref('base.res_partner_12')  # Azure Interior
        self.product_1 = self.env.ref('product.product_product_4d')  # DESK0004
        self.product_2 = self.env.ref('product.product_product_6')  # E-COM07

    def _create_fec(self, contract_no, amount, rate):
        f = Form(self.fec_model)
        f.contract_no = contract_no
        f.contract_enter_date = fields.Date.today()
        f.currency = self.currency_nzd
        f.due_date = fields.Date.today() + timedelta(days=30)
        f.rate = rate  # Against USD
        f.amount = amount
        f.reference = 'FEC Reference'
        fec = f.save()
        return fec

    def _make_supplier_invoice_form(self):
        form = Form(self.env['account.move'].with_context(default_type='in_invoice'))
        form.partner_id = self.partner
        form.currency_id = self.currency_nzd
        return form
