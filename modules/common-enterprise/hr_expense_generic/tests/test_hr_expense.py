# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import tagged
from odoo.addons.base.tests.common import SavepointCaseWithUserDemo
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


@tagged("common", "hr_expense_generic")
class TestHRExpenseSheet(SavepointCaseWithUserDemo):

    @classmethod
    def setUpClass(cls):
        super(TestHRExpenseSheet, cls).setUpClass()

        cls.company = cls.env['res.company'].create({
            'name': 'Test Company',
            'security_lead': 2.0
        })

        cls.default_account = cls.env['account.account'].create({
            'name': 'Default Account',
            'code': '7886761',
            'account_type': 'expense',
            'company_ids':  [(4, [cls.company.id])],
        })

        cls.default_journal = cls.env['account.journal'].create({
            'name': 'Default Journal',
            'type': 'general',
            'code': 'DEFJRN',
            'company_id': cls.company.id,
            'default_account_id': cls.default_account.id,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'company_id': cls.company.id,
            'property_account_payable_id': cls.default_account.id,
        })

        cls.employee = cls.env['hr.employee'].sudo().create({
            'name': 'Test Employee',
            'user_partner_id': cls.partner.id,
            'company_id': cls.company.id,
        })

        cls.payment_method = cls.env['account.payment.method'].create({
            'name': 'Test Payment Method',
            'code': 'TPM',
            'payment_type': 'outbound',
        })

        cls.payment_method_line = cls.env['account.payment.method.line'].create({
            'name': 'Test Payment Method Line',
            'payment_method_id': cls.payment_method.id,
            'journal_id': cls.default_journal.id,
        })

        cls.company.company_expense_allowed_payment_method_line_ids = [(6, 0, [cls.payment_method_line.id])]

        cls.employee_journal = cls.env['account.journal'].create({
            'name': 'Employee Expense Journal',
            'type': 'purchase',
            'code': 'EMP_EXP',
            'default_account_id': cls.default_account.id,
            'company_id': cls.company.id,
        })

        cls.expense_sheet = cls.env['hr.expense.sheet'].create({
            'name': 'Test Expense Sheet',
            'employee_id': cls.employee.id,
            'employee_journal_id': cls.employee_journal.id,
            'journal_id': cls.default_journal.id,
            'company_id': cls.company.id,
        })

    def test_default_bank_journal_id(self):
        """Test the default bank journal ID."""
        default_bank_journal_id = self.expense_sheet._default_bank_journal_id()
        self.assertEqual(
            default_bank_journal_id.id, 3,
            "The default bank journal ID should match the first allowed payment method line."
        )

    def test_payment_method_line_id_field(self):
        """Test the payment method line ID field."""
        self.expense_sheet.payment_method_line_id = self.payment_method_line.id
        self.assertEqual(
            self.expense_sheet.payment_method_line_id,
            self.payment_method_line,
            "The payment method line ID should be correctly set."
        )

    def test_get_expense_account_destination_employee_account(self):
        """Test the expense account destination for employee payment mode."""
        self.expense_sheet.payment_mode = 'company_account'
        account_dest_id = self.expense_sheet._get_expense_account_destination()
        self.assertEqual(
            account_dest_id,
            self.partner.property_account_payable_id.id,
            "The account destination should match the partner's payable account for employee payment mode."
        )

    def test_get_expense_account_destination_no_partner(self):
        """Test UserError when no partner is found for the employee."""
        self.expense_sheet.employee_id.address_id = False
        with self.assertRaises(UserError):
            self.expense_sheet._get_expense_account_destination()