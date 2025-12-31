# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.viaduct_helper import ViaductHelper


class StatementHelper(ViaductHelper):

    def company(self, company_id):
        """ Get company details.

            Note this will return the default company logo but use
            statement_logo method if you need a different logo.
        """
        company = self.env["res.company"].browse(company_id)

        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": company.name,
            "currency": company.currency_id.name,
            "gst-no": company.vat or company.partner_id.vat or "",
            "cbs-message": company.cbs_message or "",
            "address": "",
        }

        addr = company.partner_id.invoice_display_address()
        self._build_company_addr(result, "address", addr)
        self._build_partner_addr(result, "remit-address", addr)

        return result

    def statement(self, statement_id):

        statement_pool = self.env["res.partner.statement"]
        statement = statement_pool.browse(statement_id)

        result = {}
        bank_details = self._get_bank_acc_number(statement.statement_currency, statement.company_id)

        result["bank-ac-number"] = bank_details[0] or ""
        result["bank-ac-name"] = bank_details[1] or ""
        result["display_soldto"] = True

        if statement.aging == "months":
            result["month-ending"] = statement.as_at_date
            result["period-0-name"] = "Current"
            result["period-1-name"] = "1 Month"
            result["period-2-name"] = "2 Month"
            result["period-3-name"] = "3 Month +"
        else:
            days = statement.days
            result["month-ending"] = statement.date_from
            result["period-0-name"] = "Current"
            result["period-1-name"] = str(days) + " Days"
            result["period-2-name"] = str(days * 2) + " Days"
            result["period-3-name"] = "Older"
        return result

    def partner(self, partner_id):

        partner_pool = self.env["res.partner"]
        partner = partner_pool.browse(partner_id)

        result = {
            "id": partner.id,
            "name": partner.name,
            "ref": partner.ref or "",
            "payment-terms": partner.property_payment_term_id.name or "",
        }

        partner_addr = partner.invoice_display_address()
        self._build_partner_addr(result, "address", partner_addr)

        return result

    def line(self, line_id):

        line_pool = self.env["res.partner.statement.lines"]
        line = line_pool.browse(line_id)

        result = {
            "date": line.date,
            "type": line.journal_id.short_description or "",
            "invoice-number": line.invoice_number or "",
            "supplier-invoice": line.move_line.name or "",
            "customer-reference": self._customer_reference(line),
            "debit": line.debit,
            "credit": line.credit,
            "balance": line.balance,
            "blocked": line.move_line.blocked == True,  # ensure no nulls for item
            "period-0": line.period0,
            "period-1": line.period1,
            "period-2": line.period2,
            "period-3": line.period3,
            "period-4": line.period4,
        }

        return result

    def _customer_reference(self, line):
        """
        Look against the sale order.
        This requires looking at the invoice-header, and then at the associated
        invoice lines, as the line.move_id may have a sale-line relationship
        :param line:
        :return:
        """
        move = line.move_line.move_id
        if move.ref:
            return move.ref
        if move.invoice_line_ids:
            if hasattr(move.invoice_line_ids[0], 'sale_line_ids'):  # avoids dependency on sale
                move_line_with_sale_lines = move.invoice_line_ids.filtered(lambda x: x.sale_line_ids)
                if move_line_with_sale_lines:
                    return move_line_with_sale_lines[0].sale_line_ids[0].order_id.client_order_ref
        return ""

    def _build_company_addr(self, result, key, address):
        """
        :param address: company address record
        """
        self.append_non_null(result, key, address.street)
        self.append_non_null(result, key, address.street2)
        self.append_non_null(result, key, address.city)
        self.append_non_null(result, key, address.zip, ", ")

        if address.phone:
            self.append_non_null(result, key, f"p: {address.phone}")
        if address.fax:
            self.append_non_null(result, key, f"f: {address.fax}")

        if address.email:
            self.append_non_null(result, key, f"e: {address.email}")
        self.append_non_null(result, key, address.website)
        if address.vat:
            taxname = address.country_id.company_tax_name or "GST No"
            self.append_non_null(result, key, f"{taxname} : {address.vat}")

    def _build_partner_addr(self, result, key, partner):

        self.append_non_null(result, key, partner.street)
        self.append_non_null(result, key, partner.street2)
        self.append_non_null(result, key, partner.city)
        self.append_non_null(result, key, partner.zip, " ")

    def _get_bank_acc_number(self, currency, company):
        """
        @return: the bank account number for the company partner, respecting currency usage.
        @param partner: a company browse record
        """
        if not currency:
            currency = company.currency_id

        journals = self.env['account.journal'].search(
            [
                ("company_id", "=", company.id),
                ('type', '=', 'bank'),
            ])

        statement_paymode = None

        for journal in journals:
            mode_currency = journal.currency_id or company.currency_id

            if mode_currency.id == currency.id:

                # Use the payment mode marked for statements in preference,
                # otherwise the one with the first matching currency
                if journal.use_for_statement_bank_account:
                    statement_paymode = journal
                    break

                elif not statement_paymode:
                    statement_paymode = journal

        if not statement_paymode:
            # We're desperate - pick up the first payment mode
            statement_paymode = journals[0]

        return statement_paymode.bank_acc_number, statement_paymode.bank_account_id.partner_id.name
