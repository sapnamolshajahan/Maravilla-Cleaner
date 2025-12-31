# -*- coding: utf-8 -*-
import base64
import calendar
import logging

from odoo.exceptions import UserError

from odoo import fields
from .edi_generator import EDIDoc, EDIGenerator

_logger = logging.getLogger(__name__)


class Mitre10EDI(EDIGenerator):
    """
    Mitre 10 EDI Generator.
    """

    def __init__(self, env):
        super().__init__(env)

    def build_edi(self, partner, invoices):

        doc = EDIDoc()
        doc.filename = self.get_mitre10_edi_filename(partner)
        doc.subject = "Mitre 10 EDI"
        doc.data = self.create_edi(partner, invoices)
        doc.body = "EDI for the following Invoices/Credits:\n"
        for invoice in invoices:
            inv_number = "(invoice with no invoice number)"
            if invoice.name:
                inv_number = invoice.name
            doc.body += "  " + inv_number + "\n"
        return doc

    def get_edi_ref(self, partner):
        return partner.edi_reference or "unset"

    def get_m10_customer_code_name_from_sale_order(self, sale_order):
        code = sale_order.partner_shipping_id.edi_reference or "NOT SET"
        name = sale_order.partner_shipping_id.name or "NOT SET"

        return code, name

    def get_m10_customer_code_name_from_invoice(self, invoice):
        code = invoice.partner_shipping_id.edi_reference or "NOT SET"
        name = invoice.partner_shipping_id.name or "NOT SET"

        return code, name

    def get_mitre10_edi_filename(self, partner):
        prefix = self.get_edi_ref(partner)
        current_date = fields.Date.from_string(fields.Date.context_today(partner))
        return "{0}{1:02}{2:02}.txt".format(prefix, current_date.month, current_date.day)

    def get_edi_filename(self, partner, invoices):
        prefix = self.get_edi_ref(partner)
        current_date = fields.Date.from_string(fields.Date.context_today(partner))
        return "{0}{1:02}{2:02}.txt".format(prefix, current_date.month, current_date.day)

    def get_m10_invoice_ref(self, invoice):
        return invoice.ref or ""

    def create_edi(self, partner, invoices):

        # Build up the model first
        invoice_values = []
        count_invoice = 0
        total_invoice = 0.0
        count_credit = 0
        total_credit = 0.0

        # lines need to be preprocessed to get summed values
        for invoice in invoices:
            if invoice.move_type == "out_refund":
                tr_type = "C"
                count_credit += 1
            elif invoice.move_type == "out_invoice":
                tr_type = "I"
                count_invoice += 1
            else:
                return False

            invoice_lines = []
            header_total = 0.0
            header_discount = 0.0
            header_freight = 0.0

            packing_slip_number = ""
            packing_slip = invoice.picking_ids
            if packing_slip:
                packing_slip_number = packing_slip[0].name or ""
                packing_slip_number = packing_slip_number[-10:]

            # get the sale order which this invoice originated form and use the shipping contact"s edi reference as
            # the mitre 10 branch code and the name as name.
            m10_customer_code = "NOT SET"
            m10_customer_name = "NOT SET"
            source_orders = invoice.line_ids.sale_line_ids.order_id
            if len(source_orders) > 1:
                sale_order = source_orders[0]
            else:
                sale_order = source_orders
            if sale_order:
                m10_customer_code, m10_customer_name = self.get_m10_customer_code_name_from_sale_order(sale_order)
            else:
                # This is most probably a financial credit note (has no sale order origin)
                if invoice.partner_shipping_id:
                    m10_customer_code, m10_customer_name = self.get_m10_customer_code_name_from_invoice(invoice)
                else:
                    raise UserError("This Invoice/Credit Note does not have an associated sale order \
                    hence the Mitre 10 store cannot be found.\r\nPlease manually select a store by specifying the \
                    Delivery Address and try again.")

            currency = invoice.currency_id or self.env.company.currency_id
            inv_partner = invoice.partner_id

            for line in invoice.invoice_line_ids:
                prices = line.tax_ids.compute_all(line.price_unit, currency, quantity=1.0, partner=inv_partner)
                price_unit = prices['total_excluded']

                unit_nett = price_unit * (1.0 - line.discount / 100)
                if line.product_id and line.product_id.product_tmpl_id.name:
                    description = ""
                    # Construct product name, removing certain special characters
                    for character in line.product_id.product_tmpl_id.name:
                        if ord(character) < 128:
                            description += character
                else:
                    description = line.name
                line_value = unit_nett * line.quantity
                # For header value, use gst included value for running total
                gst_inc = line_value
                tax_amount = 1.0
                if line.tax_ids:
                    for tax in line.tax_ids:
                        tax_amount += (tax.amount / 100)

                gst_inc *= tax_amount

                line_map = {
                    "code": line.product_id.default_code or "",
                    "name": description,
                    "quantity": line.quantity,
                    "uom": line.product_uom_id.name or "",
                    "unit_price": price_unit,
                    "unit_price_discount": line.discount / 100 * price_unit,
                    "unit_discount": line.discount,
                    "unit_nett": unit_nett,
                    "line_value": unit_nett * line.quantity,
                }
                invoice_lines.append(line_map)

                if invoice.move_type == "out_refund":
                    total_credit += gst_inc
                elif invoice.move_type == "out_invoice":
                    total_invoice += gst_inc
                header_total += line_map["line_value"]
                header_discount += line_map["unit_price_discount"] * line.quantity

            invoice_map = {
                "transaction_type": tr_type,
                "customer_code": m10_customer_code,
                "customer_name": m10_customer_name,
                "invoice_date": invoice.invoice_date.strftime("%d%m%Y") if invoice.invoice_date else "",
                "invoice_due": invoice.invoice_date_due.strftime("%d%m%Y") if invoice.invoice_date_due else " " * 8,
                "invoice_number": invoice.name or "",
                "order_number": self.get_m10_invoice_ref(invoice=invoice),
                "total": header_total,
                "discount": header_discount,
                "freight": header_freight,
                "gst": invoice.amount_tax,
                "packing_slip": packing_slip_number,
                "lines": invoice_lines,
            }
            invoice_values.append(invoice_map)

        # Generate the EDI document
        # Preamble
        company = partner.company_id
        reference = self.get_edi_ref(partner)
        supplier_name = company.partner_id.name if company.partner_id.name else ""
        gst = company.partner_id.vat or ""
        now = fields.Date.from_string(fields.Date.context_today(partner))

        output = "0{:6.6}{:30.30}{:10.10}{}{:02d}{:02d}{:04d}{:05d}{:011.0f}{:05d}{:011.0f}{:71}\r\n".format(
            reference, supplier_name, gst.replace("-", ""),
            now.strftime("%d%m%Y"),
            calendar.monthrange(now.year, now.month)[1], now.month, now.year,
            count_invoice, total_invoice * 100,
            count_credit, total_credit * 100,
            "")

        # Lines
        for header in invoice_values:
            output += "1{} {:15.15}{:15.15}{}{:011.0f}{:09.0f}{:09.0f}{:09.0f}{:30.30}{:15.15}{}{:10}{:24}\r\n".format(
                header["transaction_type"],
                header["invoice_number"],
                header["customer_code"],
                header["invoice_date"],
                header["total"] * 100,
                header["freight"] * 100,
                header["discount"] * 100,
                header["gst"] * 100,
                header["customer_name"],
                header["order_number"],
                header["invoice_due"],
                header["packing_slip"],
                "")
            for line in header["lines"]:
                output += "2{} {:15.15}{:20.20}{:50.50}{:09.0f}{:09d}{:09.0f}{:10.10}{:09.0f}{:09.0f}{:05.0f}{:09.0f}{:09.0f}\r\n".format(
                    header["transaction_type"],
                    header["invoice_number"],
                    line["code"],
                    line["name"],
                    line["quantity"] * 1000, 0, line["quantity"] * 1000,
                    line["uom"],
                    line["unit_price"] * 1000,
                    line["unit_price_discount"] * 100,
                    line["unit_discount"] * (1000 if (line["unit_discount"] and line["unit_discount"] < 100) else 100),
                    line["unit_nett"] * 1000,
                    line["line_value"] * 100)

        # Trailer
        output += "9{:6.6}{:159}\r\n".format(reference, "")

        return base64.encodebytes(output.encode())
