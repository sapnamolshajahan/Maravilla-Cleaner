# -*- coding: utf-8 -*-
import re

from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class PurchaseOrderHelper(CommonHelper):

    def company(self, company_id):

        company = self.env["res.company"].browse(company_id)

        # base uses "Product Price", but purchase_generic_changes uses "Purchase Price"
        precision = self.env["decimal.precision"].precision_get("Purchase Price")

        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": company.name,
            "address": "",
            "price-display": "##,##0." + "0" * precision
        }

        address = company.partner_id.purchase_display_address()
        self.build_company_addr(result, "address", address)

        return result

    def purchase(self, purchase_id):
        """
        Get Associated info for the purchase order.
        """
        purchase_order = self.env["purchase.order"].browse(purchase_id)
        result = {
            "report-title": "Purchase Quotation" if purchase_order.state == "draft" else "Purchase Order",
            "order-number": purchase_order.name,
            "order-date": purchase_order.date_order,
            "supplier": purchase_order.partner_id.name,
            "supplier-code": purchase_order.partner_id.ref or "",
            "supplier-reference": purchase_order.partner_ref or "",
            "currency": purchase_order.currency_id.name,
            "currency-symbol": purchase_order.currency_id.symbol or "",
            "user": purchase_order.create_uid.sudo().name,
            "delivery-notes": purchase_order.delivery_notes or "",
            "taxes": purchase_order.amount_tax,
            "total": purchase_order.amount_total,
            "total-untaxed": purchase_order.amount_untaxed,
            "payment-terms": purchase_order.payment_term_id.name or "",
        }
        if purchase_order.date_planned:
            result["required-date"] = purchase_order.date_planned
        if purchase_order.note:
            purchase_note = re.sub(r'<.*?>', "", purchase_order.note)
            result["notes"] = purchase_note or ""
        address_supplier = purchase_order.partner_id.purchase_display_address()
        self.build_partner_addr(result, "supplier-address", address_supplier)

        if purchase_order.alternate_shipping_address:
            result["delivery-name"] = ""
            result["delivery-address"] = purchase_order.alternate_shipping_address
        else:
            (address_name, address_delivery) = self._get_delivery_address(purchase_order)
            result["delivery-name"] = address_name
            self._build_delivery_addr(result, "delivery-address", address_delivery)

        return result

    def _build_delivery_addr(self, result, key, address):
        if hasattr(address, "name"):
            self.append_non_null(result, key, address.name)

        if hasattr(address, "building"):
            self.append_non_null(result, key, address.building)
        self.build_partner_addr(result, key, address)

    def _get_delivery_address(self, purchase):
        """
        Get the delivery title and address for the purchase order.
        This method may be overridden by sub-classes.

        @return (name, res.partner address) tuple
        """
        if purchase.dest_address_id:
            name = purchase.dest_address_id.parent_id.name or purchase.dest_address_id.name
            return (name, purchase.dest_address_id)

        name = purchase.picking_type_id.warehouse_id.name
        purchase_partner = purchase.picking_type_id.warehouse_id.partner_id
        return (name, self.get_addr(purchase_partner, ["delivery"]))

    def line(self, line_id):
        purchase_line = self.env["purchase.order.line"].browse(line_id)

        if self.is_normal_line(purchase_line):
            supplier_product_code, supplier_product_name = self._get_supplier_product_info(purchase_line)
            result = {
                "description": self._format_purchase_description(purchase_line),
                "code": purchase_line.product_id.default_code or "",
                "supplier-code": supplier_product_code,
                "supplier-name": supplier_product_name,
                "uom": purchase_line.product_uom_id.name,
                "quantity": purchase_line.product_qty,
                "unit-price": purchase_line.price_unit,
                "total": purchase_line.price_subtotal,
            }
        else:
            result = {
                "description": purchase_line.name or "",
            }

        return result

    def is_normal_line(self, purchase_line):
        return not purchase_line.display_type

    def _get_supplier_product_info(self, purchase_line):

        if purchase_line.order_id.partner_id and purchase_line.product_id.product_tmpl_id.seller_ids:
            for seller_id in purchase_line.product_id.product_tmpl_id.seller_ids:
                if seller_id.partner_id == purchase_line.order_id.partner_id and seller_id.product_code:
                    return seller_id.product_code, seller_id.product_name
        return "", ""

    def _format_purchase_description(self, purchase_line):
        description_string = purchase_line.name or purchase_line.product_id.description_purchase or purchase_line.product_id.name
        return description_string.replace("[{0}]".format(purchase_line.product_id.default_code), "").strip()

    def _clean_desc(self, code, desc):
        """Trim the description output to remove the [${code}]
        """
        if not desc or not desc.strip():
            return ""
        clean = desc.replace("[{0}]".format(code), "")
        return clean.strip()
