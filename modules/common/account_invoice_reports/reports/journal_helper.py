# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class JournalHelper(CommonHelper):
    """
    Supply data for journal.jrxml
    """

    def company(self, company_id):

        company = self.env["res.company"].browse(company_id)

        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": company.name,
            "address": "",
        }

        address = company.partner_id.invoice_display_address()
        self.build_company_addr(result, "address", address)

        result.update(
            {
                "email": address.email or company.partner_id.email,
                "gst-no": address.vat or company.partner_id.vat or "",
            })

        return result

    def move(self, move_id):
        move = self.env["account.move"].browse(move_id)

        debits = credits = 0
        for line in move.line_ids:
            if not self._is_normal_line(line):
                continue
            if line.debit:
                debits += line.debit
            if line.credit:
                credits += line.credit

        result = {
            "name": move.name,
            "journal": move.journal_id.name,
            "date": move.date,
            "reference": move.ref or '',
            "amount": move.amount_total,
            "currency-name": move.currency_id.name or "",
            "currency-symbol": move.currency_id.symbol,
            "debits": debits,
            "credits": credits,
        }

        return result

    def line(self, line_id):

        line = self.env["account.move.line"].browse(line_id)

        result = {
            "name": line.name,
        }
        if self._is_normal_line(line):
            if line.credit:
                result["credit"] = line.credit
            if line.debit:
                result["debit"] = line.debit
            result.update(
                {
                    "account": "{} {}".format(line.account_id.code, line.account_id.name),
                    "amount-currency": line.amount_currency,
                    "analytic-account": "",  # TODO: somebody work this, please!
                    "currency-name": line.currency_id.name or "",
                    "currency-symbol": line.currency_id.symbol,
                })

        return result

    def _is_normal_line(self, line):
        return line.display_type == "product"
