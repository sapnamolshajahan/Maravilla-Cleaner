# -*- coding: utf-8 -*-
import logging

from odoo import _
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "sale_generic_changes")
class TestSaleChanges(common.TransactionCase):
    """Class to test sale changes  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.sale_order = self.env.ref('sale.sale_order_1')
        self.product = self.env.ref('product.product_product_6')
        bank_journal = self.env['account.journal'].create({
            'name': 'Bank',
            'code': 'BNKKK',
            'type': 'bank',
        })
        cash_journal = self.env['account.journal'].create({
            'name': _('Sale'),
            'type': 'sale',
            'code': 'OUT',
        })
        account_other = self.env['account.account'].create({
            'account_type': 'asset_current',
            'name': 'account_other',
            'code': '121040',
        })
        self.account_move_1 = self.env['account.move'].create({
            'move_type': 'entry',
            'date': '1990-01-01',
            'journal_id': bank_journal.id,
            'line_ids': [
                (0, 0, {'debit': 200.0, 'credit': 0.0, 'account_id': account_other.id,
                        'sale_line_ids': [(6, 0, self.sale_order.ids)]}),
                (0, 0, {'debit': 0.0, 'credit': 200.0, 'account_id': account_other.id,
                        'sale_line_ids': [(6, 0, self.sale_order.ids)]}),
            ],
        })
        self.account_move_2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'date': '1990-01-01',
            'journal_id': cash_journal.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'sale_line_ids': [(6,0, self.sale_order.ids)]
                }),
            ]
        })

    def test_sale_account(self):
        """
        Check sale order type 'out_invoice' in account_move
        """
        self.account_move_1._get_sale_orders()
        self.assertFalse(self.account_move_1.sale_orders)
        self.account_move_2._get_sale_orders()
        self.assertIn(self.sale_order, self.account_move_2.sale_orders)
