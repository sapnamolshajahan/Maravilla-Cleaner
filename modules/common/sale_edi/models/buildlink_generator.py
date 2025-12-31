# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime

from odoo.exceptions import UserError
from odoo.addons.base_generic_changes.utils.config import configuration

from odoo import fields
from .edi_generator import EDIDoc, EDIGenerator

_logger = logging.getLogger(__name__)

SECTION_NAME = "sftp-edi-credentials"
supplier_gln = configuration.get(SECTION_NAME, "supplier_gln", fallback="")
ftp_environment = configuration.get(SECTION_NAME, "ftp_environment", fallback="sandbox")
supplier_number = configuration.get(SECTION_NAME, "supplier_number", fallback="")
ship_to_id = configuration.get(SECTION_NAME, "ship_to_id", fallback="")


class BuildLinkEDI(EDIGenerator):
    """
    BuildLink EDI Generator.
    """

    def __init__(self, env):
        super().__init__(env)

    def build_edi(self, partner, invoices):
        doc = EDIDoc()
        doc.filename = self.get_edi_filename(partner, invoices)
        doc.subject = "BuildLink EDI"
        doc.data = self.create_edi(invoices.partner_id, invoices)
        doc.body = "EDI for the following Invoices/Credits:\n"
        for invoice in invoices:
            inv_number = "(invoice with no invoice number)"
            if invoice.name:
                inv_number = invoice.name
            doc.body += "  " + inv_number + "\n"
        return doc

    def get_edi_ref(self, partner):
        return partner.edi_reference or "unset"

    def get_buildlink_customer_code_name_from_sale_order(self, sale_order):
        code = sale_order.partner_invoice_id.edi_reference or "NOT SET"
        name = sale_order.partner_invoice_id.name or "NOT SET"

        return code, name

    def get_buildlink_customer_code_name_from_invoice(self, invoice):
        code = invoice.invoice_address.edi_reference or invoice.partner_id.edi_reference or "NOT_SET"
        name = invoice.invoice_address.name or invoice.partner_id.name or "NOT SET"

        return code, name

    def get_edi_filename(self, partner, invoice):
        prefix = self.get_edi_ref(partner)
        current_date = fields.Date.from_string(fields.Date.context_today(partner))
        if invoice.move_type == 'out_refund':
            suffix = "CREDIT"
        else:
            suffix = "INVOIC"
        return "{0}{1:02}{2:02}_{3}_{4}_{5}.txt".format(prefix, current_date.month, current_date.day, invoice.ref,
                                                        invoice.sequence_number, suffix)

    def get_buildlink_invoice_ref(self, invoice):
        return invoice.ref or ""

    def create_edi(self, partner, invoices):

        # Build up the model first
        invoice_values = []
        total_invoice = 0.0
        total_invoice_tax_inc = 0.0
        value_inc_gst = 0.0
        total_credit = 0.0
        tr_type = ""

        original_sale_order = invoices.line_ids.sale_line_ids.order_id

        # lines need to be preprocessed to get summed values
        for invoice in invoices:

            if invoice.move_type == "out_refund":
                tr_type = "C"
            elif invoice.move_type == "out_invoice":
                tr_type = "I"
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
            # the buildlink branch code and the name as name.

            source_orders = invoice.line_ids.sale_line_ids.order_id
            if len(source_orders) > 1:
                sale_order = source_orders[0]
            else:
                sale_order = source_orders

            if sale_order:
                buildlink_customer_code, buildlink_customer_name = self.get_buildlink_customer_code_name_from_sale_order(sale_order)
            else:
                # This is most probably a financial credit note (has no sale order origin)
                if invoice.invoice_address or invoice.partner_id:
                    buildlink_customer_code, buildlink_customer_name = self.get_buildlink_customer_code_name_from_invoice(invoice)
                else:
                    raise UserError("This Invoice/Credit Note does not have an associated sale order \
                    hence the BuildLink store cannot be found.\nPlease manually select a store by specifying the \
                    Delivery Address and try again.")

            for line in invoice.invoice_line_ids:
                unit_nett = line.price_unit * (1.0 - line.discount / 100)
                if line.product_id and line.product_id.name:
                    description = line.product_id.name.replace("\n", " ")
                else:
                    description = ""
                line_map = {
                    "code": line.product_id.default_code or "",
                    "name": description,
                    "quantity": int(line.quantity),
                    "uom": line.product_uom_id.name or "",
                    "unit_price": line.price_unit,
                    "unit_price_discount": line.discount / 100 * line.price_unit,
                    "unit_discount": line.discount,
                    "unit_nett": unit_nett,
                    "undiscounted_nett": line.price_unit,
                    "line_value": unit_nett * line.quantity,
                    "undiscounted_value": line.price_unit * line.quantity,
                    "barcode": line.product_id.barcode,
                    "internal_reference": line.product_id.default_code,
                    "taxes": line.product_id.taxes_id,
                    "source_sale_order": line.sale_line_ids.order_id.name
                }
                invoice_lines.append(line_map)

                if line.discount != 0.0:
                    total_invoice += line_map["line_value"]
                    line_value_inc_tax = line_map["line_value"]
                else:
                    total_invoice += line_map["line_value"] * ((100.0 - line.discount)/100.0)
                    line_value_inc_tax = line_map["line_value"] * ((100.0 - line.discount)/100.0)
                for tax in line_map["taxes"]:
                    line_value_inc_tax = (line_value_inc_tax * ((100.0 + tax.amount) / 100.0))

                    total_invoice_tax_inc += line_value_inc_tax
                header_total += line_map["line_value"]
                header_discount += line_map["unit_price_discount"] * line.quantity

            invoice_map = {
                "id": invoice.id,
                "transaction_type": tr_type,
                "customer_code": buildlink_customer_code,
                "customer_name": buildlink_customer_name,
                "invoice_date": invoice.invoice_date.strftime("%d%m%Y") if invoice.invoice_date else " ",
                "invoice_due": invoice.invoice_date_due.strftime("%d%m%Y") if invoice.invoice_date_due else " " * 8,
                "invoice_number": invoice.name or "",
                "order_number": self.get_buildlink_invoice_ref(invoice=invoice),
                "total": header_total,
                "discount": header_discount,
                "freight": header_freight,
                "packing_slip": packing_slip_number,
                "lines": invoice_lines,
            }
            invoice_values.append(invoice_map)

        # Generate the EDI document
        # Preamble
        company = self.env.company
        supplier_name = partner.name if partner.name else ""
        edi_identifier = "BUILDLINKGRP"
        date_now = fields.Date.from_string(fields.Date.context_today(partner))
        time_now = datetime.now()
        linecount = 0

        output = "UNB+UNOC:{}+{}:ZZ+{}:ZZ+{}:{}+{}'".format(
            "3" if ftp_environment == 'production' else "1",
            supplier_gln,
            edi_identifier,
            date_now.strftime("%d%m%y"),
            time_now.strftime("%H%M"),
            invoice_values[0]["id"], )

        # Initialise counts for header ID, line ID, and number of segments for final message trailer
        header_id = 1
        line_id = 0
        for header in invoice_values:
            output += "UNH+{}+INVOIC:D:96A:UN:EAN008'".format(
                header_id)
            # Increment header
            header_id += 1

            if invoices.move_type == 'out_refund':
                identifier_code = "381"
            else:
                identifier_code = "380"
            output += "BGM+{}+{}+9'".format(identifier_code, header["invoice_number"])
            formatted_date = header["invoice_date"][-4:] + header["invoice_date"][2:4] + header["invoice_date"][:2]
            output += "DTM+137:{}:102'".format(formatted_date)
            linecount += 2

            if invoice.move_type == 'out_refund':
                ref = original_sale_order.client_order_ref if original_sale_order else invoices.ref
                output += "RFF+ON:{}'".format(ref)
                linecount += 1
            else:
                # For invoice, set this to sale order number
                output += "RFF+ON:{}'".format(invoices.ref)
                linecount += 1
            if invoices.move_type == 'out_refund':
                output += "RFF+OI:{}'".format(invoices.invoice_origin)
                linecount += 1
            if header["packing_slip"] != "":
                output += "RFF+PK:{}'".format(header["packing_slip"])
                linecount += 1
            if original_sale_order:
                output += "RFF+IL:{}'".format(original_sale_order.name)
                linecount += 1

            # NAD Segment for identifying parties
            partner_address = invoices.partner_id
            invoice_address = invoices.invoice_address if invoices.invoice_address else invoices.partner_id
            try:
                output += "NAD+BT+++{}+{}".format(partner_address.name[:35], partner_address.street.replace("\n", " "))
                output += "{}+{}++{}+{}'".format(" " + partner_address.street2 if partner_address.street2 else "",
                                                     partner_address.city if partner_address.city else "",
                                                     partner_address.zip.zfill(4) if partner_address.zip else "",
                                                     partner_address.country_code if partner_address.country_code else "")
                output += "NAD+SU+{}::92++{}+{}".format(invoice_address.supplier_code if invoice_address.supplier_code else supplier_number, company.name[:35],
                                                        company.street.replace("\n", " "))

                output += "{}+{}++{}+{}'".format(
                    " " + company.street2 if company.street2 else "",
                    company.city if company.city else "",
                    company.zip.zfill(4) if company.zip else "",
                    company.country_code if company.country_code else "")
                ship_to_address = original_sale_order.partner_shipping_id if original_sale_order else invoice_address
                output += "NAD+ST+{}::92++{}+{}".format(invoice_address.store_code if invoice_address.store_code else ship_to_id, ship_to_address.name[:35],
                                                        ship_to_address.street.replace("\n", " "))
                output += "{}+{}++{}+{}'".format(" " + ship_to_address.street2 if ship_to_address.street2 else "",
                                                     ship_to_address.city if ship_to_address.city else "",
                                                     ship_to_address.zip.zfill(4) if ship_to_address.zip else "",
                                                     ship_to_address.country_code if ship_to_address.country_code else "")

                output += "NAD+RE+{}::92++{}+{}".format(invoice_address.supplier_code if invoice_address.supplier_code else supplier_number, company.name[:35],
                                                    company.street.replace("\n", " "))
                output += "{}+{}++{}+{}'".format(
                    " " + company.street2 if company.street2 else "",
                    company.city if company.city else "",
                    company.zip.zfill(4) if company.zip else "",
                    company.country_code if company.country_code else "")
                linecount += 4

            except Exception as e:
                raise UserError("Error when generating address lines. Please ensure invoice and partner addresses are "
                                "properly formatted.")

            if company.vat:
                output += "RFF+FC:{}'".format(company.vat)
                output += "RFF+AHP:{}'".format(company.vat)
                linecount += 2

            # PAT Payment Terms section

            payment_terms = invoice.invoice_payment_term_id
            fixed = False
            for payment_line in payment_terms.line_ids:
                if payment_line.delay_type != 'days_after':
                    fixed = True
            if not fixed:
                output += "PAT+3+1:::{}+5:3:D:30'".format( "Due date " + str(invoice.invoice_date_due))
            else:
                output += "PAT+1+1:::{}+5:3:D:30'".format(payment_terms.name)
            linecount += 1

            # Details of Transport; have to use attribute check as freight rate id is added field that is not default to common
            if original_sale_order:
                if hasattr(original_sale_order, 'freight_rate_id'):
                    if original_sale_order.freight_rate_id:
                        output += "TDT+20++++:::{}'".format(original_sale_order.freight_rate_id.supplier.name)
                        linecount += 1
                elif original_sale_order.delivery_count != 0:
                    carrier = "Road Freight"
                    for delivery in original_sale_order.picking_ids:
                        if delivery.carrier_id:
                            carrier = delivery.carrier_id.name
                            break
                    output += "TDT+20++++:::{}'".format(carrier)

            for line in header["lines"]:
                if not line["internal_reference"] and line["name"] == 'Cartage':
                    output += "ALC+C++++FC:::Cartage Charge'"
                    output += "MOA+8:{}{}'".format("-" if tr_type == "C" else "", line["line_value"], '.2f')
                    linecount += 1

            for line in header["lines"]:
                if line["name"] != 'Cartage':
                    line_id += 1
                    output += "LIN+{}".format(line_id)
                    if line["barcode"]:
                        output += "++{}:VP".format(line["barcode"])
                    output += "'"
                    linecount += 1
                    if line["code"]:
                        output += "PIA+1+{}:SA'".format(line["code"])
                        linecount += 1
                    if line["name"]:
                        output += "IMD+F++:::{}'".format(line["name"][:35])
                        linecount += 1
                    output += "QTY+47:{}{}:EA'".format("-" if tr_type == "C" else "", line["quantity"])
                    output += "MOA+203:{}{}'".format("-" if tr_type == "C" else "", str(format(line["line_value"], '.2f')))
                    output += "PRI+AAA:{}'".format(line["undiscounted_nett"])
                    if line["unit_discount"]:
                        output += "APR++{}:DIS'".format(line["unit_discount"])
                        linecount += 1
                    linecount += 3

        # Summary section
        output += "UNS+S'"
        output += "CNT+2:{}'".format(line_id)
        output += "MOA+86:{0}{1:.2f}'".format("-" if tr_type == "C" else "", total_invoice_tax_inc)
        output += "MOA+122:{0}{1:.2f}'".format("-" if tr_type == "C" else "", total_invoice_tax_inc)
        output += "TAX+7+GST+++:::15.00'"
        output += "MOA+124:{0}{1:.2f}'".format("-" if tr_type == "C" else "", round(total_invoice_tax_inc, 2) - total_invoice)
        output += "MOA+125:{0}{1:.2f}'".format("-" if tr_type == "C" else "", total_invoice)
        linecount += 7

        # Trailer
        output += "UNT+{}+1'".format(linecount)
        output += "UNZ+1+{}'".format(invoice_values[0]["id"])

        return base64.encodebytes(output.encode())
