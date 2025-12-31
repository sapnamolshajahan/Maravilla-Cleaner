# -*- coding: utf-8 -*-
from odoo.addons.jasperreports_viaduct.reports.common_helper import CommonHelper

from odoo import fields


class PickingHelper(CommonHelper):
    """
    Common picking helper for
    - internal-picking
    - sale-picking
    - purchase-picking
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

    def picking(self, picking_id):
        """
        Delegate to appropriate method
        """
        picking = self.env["stock.picking"].browse(picking_id)

        result = self.common_picking(picking)

        if picking.sale_id:
            return self.sale_picking(picking, result)
        if picking.purchase_id:
            return self.purchase_picking(picking, result)

        return self.internal_picking(picking, result)

    def common_picking(self, picking):
        """
        Populate the result for all picking types.
        """
        result = {
            "warehouse": ""
        }
        for move in picking.move_ids:
            if move.location_id.warehouse_id:
                result["warehouse"] = move.location_id.warehouse_id.name
                break
        return result

    def sale_picking(self, picking, result):
        """
        Populate the result for a Sale Picking.
        """
        if picking.backorder_id.name:
            result["backorder"] = picking.backorder_id.name
            result["has-backorder"] = True
        else:
            result["backorder"] = None
            result["has-backorder"] = False

        sale = picking.sale_id

        self.build_delivery_address(result, "delivery-address", sale)
        order_date = fields.Date.context_today(sale, sale.date_order)

        result.update(
            {
                "sale-order": sale.name,
                "customer-name": sale.partner_id.name,
                "customer-code": sale.partner_id.ref or "",
                "order-date": order_date,
                "user": sale.user_id.name,
                "customer-order-ref": sale.client_order_ref or "",
                "note": sale.note or "",
                "warning": sale.partner_id.picking_warn_msg or "",
            })
        if picking.scheduled_date:
            result["scheduled-date"] = self._2localtime(picking.scheduled_date)

        return result

    def purchase_picking(self, picking, result):
        """
        Populate the result for a Purchase Picking.
        """
        purchase = picking.purchase_id

        order_date = fields.Date.context_today(purchase, purchase.date_order)

        result.update(
            {
                "purchase-order": purchase.name,
                "supplier": purchase.partner_id.name,
                "creditor-code": purchase.partner_id.ref or "",
                "order-date": order_date,
                "user": purchase.user_id.name,
                "supplier-order-ref": purchase.partner_ref or "",
                "warning": purchase.partner_id.picking_warn_msg or "",
            })
        return result

    def internal_picking(self, picking, result):
        """
        Populate the result for an Internal Picking.
        """
        result.update(
            {
                "from-location": picking.location_id.warehouse_id.name or "",
                "to-location": picking.location_dest_id.warehouse_id.name or "",
                "picking-date": picking.create_date,
            })

        return result

    def move(self, move_id):
        """
        Delegate to appropriate sub-helper
        """
        move = self.env["stock.move"].browse(move_id)

        result = {
            "code": move.product_id.default_code or "",
            "uom": move.product_uom.name,
            "qty": move.product_uom_qty,
            "description": self.clean_description(move),
            "bin": "",
        }

        if move.picking_id.sale_id:
            return self.sale_move(move, result)

        return self.internal_move(move, result)

    def sale_move(self, move, result):
        """
        Populate the result for a Sale Picking move.
        """
        qty_required, on_hand, outgoing_excl_this_line, available_for_this_line = self.calculate_stock_values(move)

        result.update(
            {
                "qty-required": qty_required,
                "qty-on-hand": on_hand,
                "qty-available": available_for_this_line,
            })

        self.describe_serial_numbers(move, result, "description")

        return result

    def internal_move(self, move, result):
        """
        Populate the result for an Internal Picking move.
        """
        result.update(
            {
                "description": move.description_picking,
                "source": move.location_id.name,
                "destination": move.location_dest_id.name,
            })
        return result

    def build_delivery_address(self, result, key, sale):
        """
        Construct the delivery address for sale-pickings.

        :param result: result dictionary
        :param key: address-key
        :param sale: sale.order record
        """
        # Use a soft check for alternate-shipping address
        if hasattr(sale, "alternate_shipping_address") and sale.show_alt_delivery_address and sale.alternate_shipping_address:
            addr = ""
            for alt_address_line in sale.alternate_shipping_address.split(","):
                addr += alt_address_line.strip() + "\n"
            result[key] = addr
            return
        if sale.partner_shipping_id:
            self.build_partner_addr(result, key, sale.partner_shipping_id)
            return

        address = sale.partner_id.delivery_display_address()
        self.build_partner_addr(result, key, address)

    def calculate_stock_values(self, move):
        """
        Used by sale-pickings
        """
        qty_required = move.product_uom_qty
        on_hand = move.product_id.with_context(warehouse=move.warehouse_id.id).qty_available
        outgoing_moves_excl_this_line = self.env['stock.move'].search(
            [
                ("product_id", "=", move.product_id.id),
                ("warehouse_id", "=", move.warehouse_id.id),
                ("location_dest_id.usage", "!=", "internal"),
                ("sale_line_id", "!=", move.sale_line_id.id),
                ("state", "not in", ("done", "cancel")),
            ])
        outgoing_excl_this_line = sum([x.product_uom_qty for x in outgoing_moves_excl_this_line])
        available_for_this_line = on_hand - outgoing_excl_this_line
        return qty_required, on_hand, outgoing_excl_this_line, available_for_this_line

    def describe_serial_numbers(self, move, result, key):
        """
        Add serial numbers to result[key].

        :param move: stock.move record.
        :param result: result array.
        :param key: description key.
        :return:
        """
        serials = ""
        for line in self.env["stock.move.line"].search([("move_id", "=", move.id)]):
            if not line.lot_id and not line.lot_name:
                continue

            if serials:
                serials += ", "
            else:
                serials = "Serial Numbers: "
            serials += f"{line.lot_id.name or line.lot_name}"

        self.append_non_null(result, key, serials)

    def clean_description(self, move):
        """
        Remove product.code from the description for better display
        :param move: stock.move
        :return:
        """
        default_code = move.product_id.default_code or ""
        description = ""
        if move.product_id:
            description = move.product_id.name.replace("[{0}]".format(default_code), "").strip()
        return description
