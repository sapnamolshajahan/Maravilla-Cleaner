# -*- coding: utf-8 -*-
import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestAccountCommonPayment(common.TransactionCase):
    """Class to test account payment workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.partner1 = self.env.ref('base.res_partner_12')
        self.partner2 = self.env.ref('base.res_partner_2')
        self.account = self.env['account.account'].create({
            'name': 'Test Account',
            'code': 'TAT',
            'account_type': "asset_receivable",
        })
        bank_journal = self.env['account.journal'].create({
            'name': 'Bank',
            'code': 'BNKKK',
            'type': 'bank',
        })
        self.payment1 = self.env['account.payment'].create({
            'partner_id': self.partner1.id,
            'journal_id': bank_journal.id,
            'amount': 50.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'destination_account_id': self.account.id,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id
        })
        self.payment2 = self.env['account.payment'].create({
            'partner_id': self.partner2.id,
            'journal_id': bank_journal.id,
            'amount': 100.0,
            'payment_type': 'outbound',
            'partner_type': 'customer',
            'destination_account_id': self.account.id,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id
        })
