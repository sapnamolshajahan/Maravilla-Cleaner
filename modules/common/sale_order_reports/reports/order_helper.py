# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class SaleOrderHelper(CommonHelper):

    def company(self, company_id):

        company = self.env["res.company"].browse(company_id)

        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": company.name,
            "address": "",
            "gst-no": company.partner_id.vat,
            "notice": company.sale_order_notice,
        }

        address = company.partner_id.sales_display_address()
        self.build_company_addr(result, "address", address)

        return result

    def sale(self, sale_id):

        sale_order = self.env["sale.order"].browse(sale_id)

        result = {
            "customer-name": sale_order.partner_id.name,
            "sale-order": sale_order.get_printed_object_name(),
            "sale-order-date": sale_order.date_order,
            "salesperson": sale_order.user_id.name or "",
            "customer-order-ref": sale_order.client_order_ref or "",
            "currency-name": sale_order.currency_id.name,
            "currency-symbol": sale_order.currency_id.symbol,
            "payment-terms": sale_order.payment_term_id.name or "",
            "amount-untaxed": sale_order.amount_untaxed,
            "amount-taxed": sale_order.amount_total,
            "tax": sale_order.amount_tax,
            "note": BeautifulSoup(sale_order.note, 'html.parser').get_text() if sale_order.note else '',
        }

        self._build_invoice_addr(result, sale_order)
        self._build_delivery_addr(result, sale_order)

        if sale_order.commitment_date:
            result["delivery-date"] = sale_order.commitment_date
        if sale_order.validity_date:
            result["quote-expiry-date"] = sale_order.validity_date
        result["creator"] = self._get_create_user(sale_order)

        if sale_order.partner_id.parent_id:
            result["customer-code"] = sale_order.partner_id.parent_id.ref or ""
        else:
            result["customer-code"] = sale_order.partner_id.ref or ""

        # Label Prompts
        if sale_order.state in ("draft", "sent"):
            result["title"] = "Quotation"
            result["title-order"] = "Quotation No"
            result["title-date"] = "Quotation Date"
        else:
            result["title"] = "Sales Order"
            result["title-order"] = "Order No"
            result["title-date"] = "Order Date"

        return result

    def line(self, sale_line_id):

        line = self.env["sale.order.line"].browse(sale_line_id)

        is_normal = self.is_normal_line(line)
        result = {
            "is-normal": is_normal,
        }
        if is_normal:
            result.update(
                {
                    "description": line.name,
                    "code": line.product_id.default_code or "",
                    "clean-description": self._clean_desc(line),
                    "ordered": line.product_uom_qty,
                    "delivered": line.qty_delivered,
                    "invoiced": line.qty_invoiced,
                    "uom": line.product_uom_id.name if line.product_uom_id else "",
                    "unit-price": line.price_unit,
                    "discount": line.discount,
                    "extended": (1.0 - line.discount / 100.0) * line.price_unit * line.product_uom_qty,
                })
        elif line.display_type == "line_section":
            result["section"] = line.name
        elif line.display_type == "line_note":
            result["description"] = line.name

        return result

    def is_normal_line(self, sale_line):

        return not sale_line.display_type

    def _build_delivery_addr(self, result, sale_order):

        key = "delivery-address"
        if hasattr(sale_order, "alternate_shipping_address") and sale_order.alternate_shipping_address:
            # Alternate shipping address has been installed and
            # the alternate_shipping_address field is available
            result[key] = sale_order.alternate_shipping_address
        else:
            self.build_partner_addr(result, key, sale_order.partner_shipping_id)

    def _build_invoice_addr(self, result, sale_order):

        self.build_partner_addr(result, "invoice-address", sale_order.partner_invoice_id)

    def _get_create_user(self, sale_order):
        self.env.cr.execute("select create_uid from sale_order where id = %d" % sale_order.id)
        uid = self.env.cr.fetchone()
        if uid:
            user = self.env["res.users"].browse(uid)
            return user.name or ""
        return ""

    def _clean_desc(self, line):
        """
        Description that doesn't have embedded product-code.
        :param line:
        :return:
        """
        return line.name.replace("[{}]".format(line.product_id.default_code), "").strip()
