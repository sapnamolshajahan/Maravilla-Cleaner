# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class RemittanceAdviceHelper(CommonHelper):

    def company(self, company_id):

        company = self.env["res.company"].browse(company_id)
        partner = company.partner_id
        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": self._get_name(partner).name,
            "website": company.website or "",
            "address": "",
        }

        address = partner.invoice_display_address()
        self.build_company_addr(result, "address", address)

        result.update(
            {
                "email": address.email or company.partner_id.email,
                "gst": address.vat or company.partner_id.vat or ""
            })
        return result

    def _get_name(self, partner):
        """
        @return: a res.partner.name browse record of parent partner (if exists) or partner
        @param partner: usually latest partner browse record - "o"
        """
        return partner.parent_id or partner

    def customer(self, customer_id):

        result = {}

        customer = self.env["res.partner"].browse(customer_id)
        result["name"] = self._get_name(customer).name

        self.build_partner_addr(result, "address", self.get_addr(customer, "payment"))

        return result

    def payment(self, payment_id):

        payment = self.env["account.payment"].browse(payment_id)

        result = {
            "reference": payment.name or '--',
            "currency-name": payment.currency_id.name,
            "currency-symbol": payment.currency_id.symbol,
        }
        if payment.date:
            result["date"] = payment.date

        return result

    def payment_line(self, line_id):

        line = self.env["account.payment"].browse(line_id)

        invoice, paid = self.paid_amount(line)
        result = {
            "invoice-date": invoice.invoice_date or invoice.date or "",
            "paid-amount": paid,
        }

        if line.move_id.name:
            result["your-reference"] = invoice.ref
        else:
            result["your-reference"] = "Unallocated"

        if line.move_id.currency_id and line.move_id.currency_id != self.env.company.currency_id:
            amount = 0 - line.move_id.amount_total_in_currency_signed
        else:
            amount = line.move_id.amount_total

        result["invoice-amount"] = amount

        if line.move_id.currency_id and line.move_id.currency_id != self.env.company.currency_id:
            result["currency"] = line.move_id.currency_id.name or ""
        else:
            result["currency"] = ""

        return result

    def paid_amount(self, payment):
        """
        :param payment: account.payment
        :return: (invoice:account.move, paid-amount)
        """
        apr_model = self.env["account.partial.reconcile"]
        invoice = self.env["account.move"]

        credit = debit = 0
        for move_line in payment.move_id.line_ids:
            if move_line.account_id.account_type not in ("asset_receivable", "liability_payable"):
                continue

            partials = apr_model.search(
                [
                    "|",
                    ("debit_move_id", "=", move_line.id),
                    ("credit_move_id", "=", move_line.id),
                ])
            for apr in partials:
                debit += apr.debit_amount_currency or 0
                credit += apr.credit_amount_currency or 0
                invoice = apr.credit_move_id.move_id

        return (invoice, debit if invoice.amount_total_in_currency_signed > 0 else credit)
