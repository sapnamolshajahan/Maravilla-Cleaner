# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tests import Form, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestResPartnerStatement(TransactionCase):

    def setUp(self):
        super(TestResPartnerStatement, self).setUp()
        self.ResPartnerStatement = self.env['res.partner.statement']
        self.ResPartner = self.env['res.partner']
        self.AccountMove = self.env['account.move']
        self.AccountAccount = self.env['account.account']
        self.AccountJournal = self.env['account.journal']
        self.ResCompany = self.env['res.company']
        self.Currency = self.env['res.currency']

        # Setup company
        self.company = self.env.company
        self.company_currency = self.company.currency_id

        # Setup partners
        self.customer = self.ResPartner.create({
            'name': 'Test Customer',
            'is_company': True,
            'customer': True,
        })
        self.supplier = self.ResPartner.create({
            'name': 'Test Supplier',
            'is_company': True,
            'supplier': True,
        })

        # Setup accounts
        self.receivable_account = self.AccountAccount.search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', '=', self.company.id),
        ], limit=1)
        self.payable_account = self.AccountAccount.search([
            ('account_type', '=', 'liability_payable'),
            ('company_ids', '=', self.company.id),
        ], limit=1)
        # Setup journals
        self.sale_sequence = self.env['ir.sequence'].create({
            'name': 'Sales Journal Sequence',
            'implementation': 'no_gap',
            'prefix': 'INV/',
            'padding': 5,
            'company_id': self.company.id,
        })
        self.sales_journal = self.env['account.journal'].create({
            'name': 'Sales Journal',
            'type': 'sale',
            'code': 'SAL',
            'sequence_id': self.sale_sequence.id,
            'company_id': self.company.id,
        })


        # self.sales_journal = self.AccountJournal.search([
        #     ('type', '=', 'sale'),
        #     ('company_id', '=', self.company.id),
        #
        # ], limit=1)
        self.purchase_journal = self.AccountJournal.search([
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company.id),
        ], limit=1)

        # Setup currencies
        self.usd = self.Currency.search([('name', '=', 'USD')], limit=1)
        if not self.usd:
            self.usd = self.Currency.create({
                'name': 'USD',
                'symbol': '$',
                'rounding': 0.01,
            })
        self.eur = self.Currency.search([('name', '=', 'EUR')], limit=1)
        if not self.eur:
            self.eur = self.Currency.create({
                'name': 'TEST',
                'symbol': '€',
                'rounding': 0.01,
            })

        # Ensure rates are set
        self.env['res.currency.rate'].create({
            'name': date.today(),
            'currency_id': self.usd.id,
            'rate': 1.5,
            'company_id': self.company.id,
        })
        self.env['res.currency.rate'].create({
            'name': date.today(),
            'currency_id': self.eur.id,
            'rate': 0.5,
            'company_id': self.company.id,
        })

    def create_invoice(self, partner, account, journal, currency=None, amount=100, date_invoice=None):
        """ Helper to create an invoice """
        move_form = self.env['account.move'].with_context(default_move_type='out_invoice').create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'currency_id': currency.id if currency else self.company_currency.id,
            'invoice_date': date_invoice or date.today(),
            'journal_id':journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'quantity': 1,
                'price_unit': amount,
                'account_id': account.id,
            })],
        })
        move_form.action_post()
        return move_form

    def test_wizard_defaults(self):
        """ Test wizard default values """
        wizard = self.ResPartnerStatement.create({})
        self.assertEqual(wizard.company_id, self.env.company)
        self.assertEqual(wizard.as_at_date, date.today())
        self.assertEqual(wizard.statement_currency, self.env.company.currency_id)

    def test_onchange_type(self):
        """ Test onchange for type field sets correct partner domain """
        wizard = self.ResPartnerStatement.new({'type': 'asset_receivable'})
        wizard._onchange_type()
        domain = wizard._fields['partner_ids'].domain(wizard)
        self.assertIn(('customer', '=', True), domain)

        wizard.type = 'liability_payable'
        wizard._onchange_type()
        domain = wizard._fields['partner_ids'].domain(wizard)
        self.assertIn(('supplier', '=', True), domain)

    def test_generate_customer_statement(self):
        """ Test generating a statement for a customer with an invoice """
        invoice = self.create_invoice(self.customer, self.receivable_account, self.sales_journal, amount=200)
        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
        })
        wizard._do_report('res.partner.statement')
        self.assertTrue(wizard.line_ids)
        line = wizard.line_ids[0]
        self.assertEqual(line.balance, 200.0)

    def test_aged_balance_calculation(self):
        """ Test aging buckets are correctly calculated """
        old_date = date.today() - relativedelta(months=3)
        invoice = self.create_invoice(self.customer, self.receivable_account, self.sales_journal, date_invoice=old_date)
        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
            'aging': 'months',
        })
        wizard._do_report('aged.trial.balance.xls.report')
        line = wizard.line_ids.filtered(lambda l: l.move_line == invoice.line_ids[0])
        self.assertEqual(line.period3, 200.0, "Invoice should be in period 3")

    def test_currency_conversion(self):
        """ Test transactions in foreign currency are converted correctly """
        invoice = self.create_invoice(self.customer, self.receivable_account, self.sales_journal, currency=self.usd,
                                      amount=100)
        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
            'statement_currency': self.company_currency.id,
        })
        wizard._do_report('res.partner.statement')
        line = wizard.line_ids[0]
        # 100 USD * 1.5 rate = 150 company currency
        self.assertEqual(line.balance, 150.0)

    def test_exclude_reconciled(self):
        """ Test reconciled entries are excluded when flag is set """
        invoice = self.create_invoice(self.customer, self.receivable_account, self.sales_journal)
        payment = self.env['account.move'].create({
            'move_type': 'entry',
            'date': date.today(),
            'journal_id': self.sales_journal.id,
            'line_ids': [
                (0, 0, {
                    'account_id': self.receivable_account.id,
                    'partner_id': self.customer.id,
                    'credit': 200.0,
                }),
                (0, 0, {
                    'account_id': self.company.default_account_id.id,
                    'debit': 200.0,
                }),
            ],
        })
        payment.action_post()
        (invoice.line_ids + payment.line_ids).filtered(lambda l: l.account_id == self.receivable_account).reconcile()

        # Test with reconcil=False
        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
            'reconcil': False,
        })
        wizard._do_report('res.partner.statement')
        self.assertFalse(wizard.line_ids, "Reconciled lines should be excluded")

        # Test with reconcil=True
        wizard.reconcil = True
        wizard._do_report('res.partner.statement')
        self.assertTrue(wizard.line_ids, "Reconciled lines should be included")

    def test_zero_balance_exclusion(self):
        """ Test zero balance partners are excluded when zero_balance is False """
        invoice = self.create_invoice(self.customer, self.receivable_account, self.sales_journal)
        payment = self.env['account.move'].create({
            'move_type': 'entry',
            'date': date.today(),
            'journal_id': self.sales_journal.id,
            'line_ids': [
                (0, 0, {
                    'account_id': self.receivable_account.id,
                    'partner_id': self.customer.id,
                    'credit': 200.0,
                }),
                (0, 0, {
                    'account_id': self.company.default_account_id.id,
                    'debit': 200.0,
                }),
            ],
        })
        payment.action_post()
        (invoice.line_ids + payment.line_ids).filtered(lambda l: l.account_id == self.receivable_account).reconcile()

        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
            'zero_balance': False,
        })
        wizard._do_report('res.partner.statement')
        self.assertFalse(wizard.line_ids, "Zero balance should be excluded")

    def test_error_no_partners(self):
        """ Test error raised when no partners selected """
        with self.assertRaises(UserError):
            wizard = self.ResPartnerStatement.create({})
            wizard._do_report('res.partner.statement')

    def test_email_statement(self):
        """ Test emailing statements to partners with correct settings """
        self.customer.write({'email': 'test@example.com'})
        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
            'send_email': True,
        })
        # Assuming email sending is mocked or tested separately
        wizard.email_statement()
        # Check if email job is queued
        emails = self.env['res.partner.statement.email'].search([('partner_id', '=', self.customer.id)])
        self.assertTrue(emails, "Email should be queued for the partner")

    def test_background_task(self):
        """ Test report generation in background task """
        self.create_invoice(self.customer, self.receivable_account, self.sales_journal)
        wizard = self.ResPartnerStatement.create({
            'partner_ids': [(6, 0, [self.customer.id])],
            'type': 'asset_receivable',
            'as_at_date': date.today(),
            'run_as_task': True,
        })
        result = wizard.print_statement()
        self.assertEqual(result['type'], 'ir.actions.act_window_close', "Task should be submitted")