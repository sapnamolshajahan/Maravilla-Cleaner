# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class BasicInvoiceHelper(CommonHelper):
    """
    This invoice helper supplies data for:
        1. invoice.jrxml
        2. credit.jrxml
    """

    def company(self, company_id):

        company = self.env["res.company"].browse(company_id)

        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": company.name,
            "website": company.website or "",
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

    def invoice(self, invoice_id):

        invoice = self.env["account.move"].browse(invoice_id)

        result = {
            "invoice-number": invoice.name or "",
            "partner-name": invoice.partner_id.name,
            "partner-code": invoice.partner_id.ref or "",
            "salesperson": invoice.user_id.name,
            "customer-code": invoice.partner_id.ref or "",
            "customer-reference": invoice.ref or "",
            "comment": invoice.narration or None,
            "amount-untaxed": invoice.amount_untaxed,
            "amount-tax": invoice.amount_tax,
            "amount-total": invoice.amount_total,
            "amount-unpaid": invoice.amount_residual_signed,
            "amount-paid": invoice.amount_total - invoice.amount_residual_signed,
            "currency-name": invoice.currency_id.name,
            "currency-symbol": invoice.currency_id.symbol,
        }
        if invoice.invoice_date:
            result["invoice-date"] = invoice.invoice_date
        if invoice.invoice_date_due:
            result["invoice-date-due"] = invoice.invoice_date_due

        # Hide/Show Discount values
        result["has-discount"] = False
        for line in invoice.invoice_line_ids:
            if line.discount:
                result["has-discount"] = True
                break

        # Addresses
        address_partner = invoice.partner_id.invoice_display_address()
        self.build_partner_addr(result, "partner-address", address_partner)

        result["customer-order-ref"] = self._get_customer_reference(invoice)
        tandc = result["comment"]
        result["comment"] = BeautifulSoup(tandc, 'html.parser').get_text() if tandc else ''

        result["original-invoice-number"] = ""
        if invoice.move_type != "out_invoice" and invoice.amount_total_signed < 0:

            # Credit Note
            if hasattr(invoice, 'sale_order_id'):
                if invoice.sale_order_id:
                    origin_invoice = self.env['account.move'].search(
                        [
                            ("sale_order_id", "=", invoice.sale_order_id.id),
                            ("move_type", "=", "out_invoice")
                        ], limit=1)

                    if origin_invoice:
                        result["original-invoice-number"] = origin_invoice.name
                    else:
                        result["original-invoice-number"] = invoice.invoice_origin or ""  # best guess

        result["payment-terms"] = "Payment due 20th of the month"
        if invoice.invoice_payment_term_id:
            result["payment-terms"] = invoice.invoice_payment_term_id.name
            if invoice.invoice_date_due and invoice.invoice_payment_term_id.note:
                result["payment-terms"] = "{n} and due on {d}".format(n=invoice.invoice_payment_term_id.note,
                                                                      d=invoice.invoice_date_due.strftime("%d-%m-%y"))
        elif invoice.partner_id.property_payment_term_id:
            result["payment-terms"] = invoice.partner_id.property_payment_term_id.note or ""

        note = result["payment-terms"]
        result["payment-terms"] = BeautifulSoup(note, 'html.parser').get_text()

        bank, account_number, bank_journal = self._get_bank_details(invoice)

        # handle exception where invoice is not local currency but we have no bank account in that currency

        if (bank_journal and invoice.currency_id.id != bank_journal.currency_id.id and
                invoice.currency_id.id != self.env.company.currency_id.id):
            result.update(
                {
                    "bank-name": bank.bank_name or "",
                    "bank-swift": bank.swift or "",
                    "bank-ac-name": bank.partner_id.name or "",
                    "bank-ac-number": bank.acc_number + ' Bank SWIFT: ' + bank.swift,
                })

        elif bank:
            result.update(
                {
                    "bank-name": bank.bank_name or "",
                    "bank-swift": bank.swift or "",
                    "bank-ac-name": bank.partner_id.name or "",
                    "bank-ac-number": account_number or bank.acc_number or "",
                })
        else:
            result.update(
                {
                    "bank-name": "",
                    "bank-swift": "",
                    "bank-ac-name": "",
                    "bank-ac-number": account_number or "",
                })
        return result

    def line(self, line_id):

        line = self.env["account.move.line"].browse(line_id)

        result = {
            "code": line.product_id.default_code or "",
            "description": self._clean_desc(line.product_id.default_code, line.name),
        }
        if self._is_normal_line(line):
            result.update(
                {
                    "quantity": line.quantity,
                    "uom": line.product_uom_id.name or "",
                    "unit-price": line.price_unit,
                    "price-subtotal": line.price_subtotal,
                    "discount": line.discount,
                    "extended": line.price_subtotal,
                })
        return result

    def _is_normal_line(self, line):
        return line.display_type == "product"

    def _clean_desc(self, product_code, desc):

        if not desc:
            return ""

        if not product_code:
            return desc.strip()

        scrubbed = desc.replace("[{0}]".format(product_code), "")
        return scrubbed.strip()

    def _get_bank_details(self, invoice):
        """
        Get Bank details that are to be associated with the invoice
        by matching currency details.

        @return: res.partner.bank or None
        """
        company = invoice.company_id
        currency_id = invoice.currency_id.id or company.currency_id.id

        currency_journals = []

        # Find journals for the same currency and type=bank
        bank_journals = self.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", '=', company.id)
            ])

        for journal in bank_journals:
            currency = journal.currency_id or company.currency_id

            if currency.id == currency_id:
                if journal.use_for_statement_bank_account:
                    currency_journals = [journal]
                    break
                else:
                    currency_journals.append(journal)

        for journal in currency_journals:
            return journal.bank_account_id, journal.bank_account_for_invoice, journal

        # handle if not local invoice but no bank account in same currency
        if bank_journals:
            return bank_journals[0].bank_account_id, bank_journals[0].bank_account_for_invoice, bank_journals[0]

        return None, None, None

    def _get_customer_reference(self, invoice):
        """
        Get the customer reference for different types of invoices
        :param invoice: account invoice browse record.
        :returns Customer reference
        """
        return invoice.ref or invoice.invoice_origin or ""
