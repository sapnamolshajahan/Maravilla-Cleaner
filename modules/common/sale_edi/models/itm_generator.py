# -*- coding: utf-8 -*-
import base64
import logging
from datetime import datetime

from odoo.exceptions import UserError
from odoo.addons.base_generic_changes.utils.config import configuration

from odoo import fields
from .edi_generator import EDIDoc, EDIGenerator

_logger = logging.getLogger(__name__)

SECTION_NAME = "ftp-edi-credentials"
supplier_gln = configuration.get(SECTION_NAME, "supplier_gln", fallback="")
ftp_environment = configuration.get(SECTION_NAME, "ftp_environment", fallback="sandbox")


class ItmEDI(EDIGenerator):
    """
    ITM EDI Generator.
    """

    def __init__(self, env):
        super().__init__(env)

    def build_edi(self, partner, invoices):

        doc = EDIDoc()
        doc.filename = self.get_edi_filename(partner, invoices)
        doc.subject = "ITM EDI"
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

    def get_itm_customer_code_name_from_sale_order(self, sale_order):
        code = sale_order.partner_invoice_id.edi_reference or "NOT SET"
        name = sale_order.partner_invoice_id.name or "NOT SET"

        return code, name

    def get_itm_customer_code_name_from_invoice(self, invoice):
        code = invoice.invoice_address.edi_reference or "NOT SET"
        name = invoice.invoice_address.name or "NOT SET"

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

    def get_itm_invoice_ref(self, invoice):
        return invoice.ref or ""

    def create_edi(self, partner, invoices):

        # Build up the model first
        invoice_values = []
        total_invoice = 0.0
        total_invoice_tax_inc = 0.0
        value_inc_gst = 0.0
        total_credit = 0.0

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
            # the itm branch code and the name as name.

            source_orders = invoice.line_ids.sale_line_ids.order_id
            if len(source_orders) > 1:
                sale_order = source_orders[0]
            else:
                sale_order = source_orders

            if sale_order:
                itm_customer_code, itm_customer_name = self.get_itm_customer_code_name_from_sale_order(sale_order)
            else:
                # This is most probably a financial credit note (has no sale order origin)
                if invoice.invoice_address:
                    itm_customer_code, itm_customer_name = self.get_itm_customer_code_name_from_invoice(invoice)
                else:
                    raise UserError("This Invoice/Credit Note does not have an associated sale order \
                    hence the ITM store cannot be found.\r\nPlease manually select a store by specifying the \
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
                    "quantity": line.quantity,
                    "uom": line.product_uom_id.name or "",
                    "unit_price": line.price_unit,
                    "unit_price_discount": line.discount / 100 * line.price_unit,
                    "unit_discount": line.discount,
                    "unit_nett": unit_nett,
                    "line_value": unit_nett * line.quantity,
                    "barcode": line.product_id.barcode,
                    "internal_reference": line.product_id.default_code,
                    "taxes": line.product_id.taxes_id,
                    "source_sale_order": line.sale_line_ids.order_id.name
                }
                invoice_lines.append(line_map)

                # if invoice.move_type == "out_refund":
                #     total_credit += line_map["line_value"]
                # elif invoice.move_type == "out_invoice":
                total_invoice += line_map["line_value"]
                line_value_inc_tax = line_map["line_value"]
                for tax in line_map["taxes"]:
                    line_value_inc_tax = (line_value_inc_tax * ((100.0 + tax.amount) / 100.0))

                    total_invoice_tax_inc += line_value_inc_tax
                header_total += line_map["line_value"]
                header_discount += line_map["unit_price_discount"] * line.quantity

            invoice_map = {
                "id": invoice.id,
                "transaction_type": tr_type,
                "customer_code": itm_customer_code,
                "customer_name": itm_customer_name,
                "invoice_date": invoice.invoice_date.strftime("%d%m%Y") if invoice.invoice_date else " ",
                "invoice_due": invoice.invoice_date_due.strftime("%d%m%Y") if invoice.invoice_date_due else " " * 8,
                "invoice_number": invoice.name or "",
                "order_number": self.get_itm_invoice_ref(invoice=invoice),
                "total": header_total,
                "discount": header_discount,
                "freight": header_freight,
                "packing_slip": packing_slip_number,
                "lines": invoice_lines,
            }
            invoice_values.append(invoice_map)

        # Generate the EDI document
        # Preamble
        company = partner.company_id
        supplier_name = partner.name if partner.name else ""
        if ftp_environment == 'production':
            edi_identifier = "ITMGROUP"
        else:
            edi_identifier = "TST1ITMGROUP"
        date_now = fields.Date.from_string(fields.Date.context_today(partner))
        time_now = datetime.now()

        output = "UNA:+.? '\nUNB+UNOC:3+{}:ZZ+{}:ZZ+{}:{}+{}'\n".format(
            supplier_gln,
            edi_identifier,
            date_now.strftime("%d%m%y"),
            time_now.strftime("%H%M"),
            invoice_values[0]["id"],)

        # Initialise counts for header ID, line ID, and number of segments for final message trailer
        header_id = 1
        line_id = 1
        for header in invoice_values:
            output += "UNH+{}+INVOIC:D:96A:UN:EAN008'\n".format(
                header_id)
            # Increment header
            header_id += 1
            if invoices.move_type == 'out_refund':
                identifier_code = "381"
            else:
                identifier_code = "380"
            output += "BGM+{}+{}+9'\n".format(identifier_code, header["invoice_number"])
            formatted_date = header["invoice_date"][-4:] + header["invoice_date"][2:4] + header["invoice_date"][:2]
            output += "DTM+137:{}:102'\r\n".format(formatted_date)

            if invoice.move_type == 'out_refund':
                ref = original_sale_order.client_order_ref if original_sale_order else invoices.ref
                output += "RFF+ON:{}'\r\n".format(ref)
            else:
                # For invoice, set this to sale order number
                output += "RFF+ON:{}'\r\n".format(invoices.ref)
            if invoices.move_type == 'out_refund':
                output += "RFF+OI:{}'\r\n".format(invoices.invoice_origin)
            if header["packing_slip"] != "":
                output += "RFF+PK:{}'\r\n".format(header["packing_slip"])

            # NAD Segment for identifying parties
            address = invoices.invoice_address
            partner_address = invoices.partner_id
            if not address:
                address = invoices.partner_id
            try:
                output += "NAD+BT+ITM::92++{}+{}".format(partner_address.name[:35], partner_address.street.replace("\n", " "))
                output += "{}+{}++{}+{}'\r\n".format(" " + partner_address.street2 if partner_address.street2 else "",
                                               partner_address.city if partner_address.city else "",
                                               partner_address.zip.zfill(4) if partner_address.zip else "",
                                               partner_address.country_code if partner_address.country_code else "")
                output += "NAD+SU+{}::92++{}+{}".format(address.supplier_code, supplier_name[:35], partner.street.replace("\n", " "))
                output += "{}+{}++{}+{}'\r\n".format(" " + address.street2 if address.street2 else "",
                                               address.city if address.city else "",
                                               address.zip.zfill(4) if address.zip else "",
                                               address.country_code if address.country_code else "")
                ship_to_address = original_sale_order.partner_shipping_id if original_sale_order else address
                output += "NAD+ST+{}::92++{}+{}".format(address.store_code, ship_to_address.name[:35],
                                                        ship_to_address.street.replace("\n", " "))
                output += "{}+{}++{}+{}'\r\n".format(" " + ship_to_address.street2 if ship_to_address.street2 else "",
                                                     ship_to_address.city if ship_to_address.city else "",
                                                     ship_to_address.zip.zfill(4) if ship_to_address.zip else "",
                                                     ship_to_address.country_code if ship_to_address.country_code else "")
            except Exception:
                raise UserError("Error when generating address lines. Please ensure invoice and partner addresses are "
                                "properly formatted.")

            # If currency is defined, will use that name (NZD/AUD), otherwise default to NZD
            if company.currency_id.name:
                output += "CUX+2:{}:4'\r\n".format(company.currency_id.name)
            else:
                output += "CUX+2:NZD:4'\r\n"

            for line in header["lines"]:
                output += "LIN+{}".format(line_id)
                if line["barcode"]:
                    output += "++{}:EN".format(line["barcode"])
                elif line["code"]:
                    output += "++{}:EN".format(line["code"])
                output += "'\r\n"
                if line["internal_reference"]:
                    output += "PIA+5+{}:SA'\r\n".format(line["internal_reference"])
                elif not line["internal_reference"] and line["name"] == 'Cartage':
                    output += "PIA+5+CARTAGE:SA'\r\n"
                if line["name"]:
                    output += "IMD+F++:::{}'\r\n".format(line["name"][:35])
                output += "QTY+47:{}:EA'\r\n".format(line["quantity"])
                output += "MOA+128:{}'\r\n".format(str(format(line["line_value"], '.2f')))
                for tax in line["taxes"]:
                    if tax.type_tax_use == "sale":
                        value_inc_gst = (float(line["line_value"]) * ((100.0 + tax.amount)/100.0))
                    output += "MOA+77:{0:.2f}'\r\n".format(value_inc_gst)
                output += "PRI+AAA:{}'\r\n".format(line["unit_nett"])
                for tax in line["taxes"]:
                    if tax.type_tax_use == "sale":
                        output += "TAX+7+GST+++:::{0:.2f}'\r\n".format(tax.amount)
                line_id += 1

        # Summary section
        output += "UNS+S'\r\n"
        output += "CNT+2:{}'\r\n".format(line_id)
        output += "MOA+128:{0:.2f}'\r\n".format(total_invoice)
        output += "MOA+77:{0:.2f}'\r\n".format(total_invoice_tax_inc)
        output += "TAX+7+GST+++:::15.00'\r\n"
        output += "MOA+124:{0:.2f}'\r\n".format(total_invoice_tax_inc - total_invoice)

        # Trailer
        nlines = output.count("\n")
        output += "UNT+{}+1'\r\n".format(nlines - 1)
        output += "UNZ+1+{}'\r\n".format(invoice_values[0]["id"])

        return base64.encodebytes(output.encode())
