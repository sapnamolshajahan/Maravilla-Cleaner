# -*- coding: utf-8 -*-
import re

from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper


class PaymentOrderHelper(ViaductHelper):

    def company(self, company_id):
        result = {"logo": self.env.company.logo}
        return result

    def format_date(self, date):
        return date.strftime('%d/%m/%Y') if date else ''

    def payment(self, payment_id):
        result = {}
        payment = self.env["account.batch.payment"].browse(payment_id)
        partner_bank = payment.journal_id.bank_account_id
        result["bank-account"] = partner_bank.acc_number

        check_total = 0
        used_accounts = []

        for line in payment.payment_ids:

            if not line.partner_bank_id.acc_number:
                continue

            ac_num = re.sub("[^0-9]", "", line.partner_bank_id.acc_number)
            if len(ac_num) > 13:
                ac_no = int(ac_num)
                branch = int(ac_num[2:6])
                account = int(ac_num[6:13])

                if branch and account and ac_no not in used_accounts:
                    check_total += int(ac_num[2:13])
                    used_accounts.append(ac_no)

        check_total = check_total % 100000000000
        check_str = str(check_total).zfill(11)[-11:]
        result["checksum"] = check_str
        result["date-created"] = self.format_date(payment.create_date)
        result["date-action"] = self.format_date(payment.date)
        result["date-done"] = self.format_date(payment.date)
        result["payment-type"] = payment.batch_type
        return result

    def payment_line(self, line_id):
        result = {}

        line = self.env["account.payment"].browse(line_id)
        result["partner"] = line.partner_id.name

        if line.move_id:
            result["invoice-amount"] = line.move_id.amount_total or 0.01
        else:
            result["invoice-amount"] = ""

        result["customer-reference"] = line.move_id.ref
        result["amount"] = line.amount
        result["customer-bank-account"] = line.partner_bank_id and line.partner_bank_id.acc_number or ""

        if line.move_id and line.currency_id != line.move_id.company_currency_id:
            result["currency"] = line.currency_id.name
            result["currency-amount"] = "{0:.2f}".format(line.amount)
            result["has-currency"] = True
        else:
            result["currency"] = ""
            result["currency-amount"] = ""
            result["has-currency"] = False

        return result
