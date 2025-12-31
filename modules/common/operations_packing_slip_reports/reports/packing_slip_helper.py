# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper


class PackingSlipHelper(CommonHelper):

    def company(self, company_id):
        company = self.env["res.company"].browse(company_id)

        result = {
            "logo-path": self.image_path(company, "logo"),
            "name": company.name,
            "address": "",
            "gst-no": company.partner_id.vat or "",
        }

        invoice_address = self.get_addr(company.partner_id, "invoice")
        self.build_company_addr(result, "address", invoice_address)

        return result

    def picking(self, picking_id):

        picking = self.env["stock.picking"].browse(picking_id)

        result = {
            "name": picking.name,
            "sale-order": picking.sale_id.name or "",
            "salesperson": self.get_create_user(picking.sale_id),
            "customer-code": picking.sale_id.partner_id.ref or "",
            "customer-order-ref": picking.sale_id.client_order_ref or "",
            "carrier": picking.carrier_id.name or "",
            "tracking-ref": picking.carrier_tracking_ref or "",
            "note": picking.note or "",
            "deliver-name": picking.sale_id.partner_id.name or "",
        }
        if picking.carrier_price:
            self.append_non_null(result, "note", f"Shipment includes freight of ${picking.carrier_price:0.2f}")

        if picking.sale_id:
            sale_order = picking.sale_id
            result.update(
                {
                    "currency-name": sale_order.currency_id.name,
                    "currency-symbol": sale_order.currency_id.symbol,
                    "amount-untaxed": sale_order.amount_untaxed,
                    "amount-tax": sale_order.amount_tax,
                    "amount-total": sale_order.amount_total,
                })

        # Delivery details
        if picking.sale_id:
            result["deliver-name"] = picking.sale_id.partner_id.name or ""
            self.build_delivery_address(result, "deliver-to", picking.sale_id)
        else:
            result["deliver-name"] = picking.partner_id.name or ""
            self.build_partner_addr(result, "deliver-to", picking.partner_id)

        if picking.date_done:
            result["despatch-date"] = picking.date_done

        result["warehouse"] = ""
        for move in picking.move_ids:
            if move.location_id:
                result["warehouse"] = move.location_id.warehouse_id.name
                break

        return result

    def move(self, move_id):

        move = self.env["stock.move"].browse(move_id)

        result = {
            "item": move.product_id.default_code or "",
            "description": move.description_picking or move.name,
            "ordered": move.sale_line_id.product_uom_qty or 0,
            "supplied": move.quantity,
            "done": move.sale_line_id.qty_delivered,
            "uom": move.product_uom.name,
            "unit-price": move.sale_line_id.price_unit or 0,
            "discount": move.sale_line_id.discount or 0,
        }
        result["todo"] = result["ordered"] - result["done"]
        result["extended"] = self.move_value(move)

        return result

    def move_value(self, move):

        unit_price = move.sale_line_id.price_unit or 0
        discount = move.sale_line_id.discount or 0
        return (1.0 - discount / 100.0) * unit_price * move.product_qty

    def build_delivery_address(self, result, key, sale):
        """
        Has implicit dependency on sale_alternate shipping_address
        """
        if sale.show_alt_delivery_address and sale.alternate_shipping_address:
            for alt_address_line in sale.alternate_shipping_address.split(","):
                if key in result:
                    result[key] += alt_address_line.strip() + "\n"
                else:
                    result[key] = alt_address_line.strip() + "\n"
            return
        if sale.partner_shipping_id.street:
            self.build_partner_addr(result, key, sale.partner_shipping_id)
        else:
            result[key] = " "

    def get_create_user(self, sale_order):
        username = ""
        if sale_order:
            if sale_order.user_id:
                username = sale_order.user_id.name
            else:
                user = sale_order.create_uid
                username = user.name or ""

        return username
