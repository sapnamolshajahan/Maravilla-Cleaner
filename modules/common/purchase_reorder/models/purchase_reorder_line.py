from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

import logging

_log = logging.getLogger(__name__)


class PurchaseReorderLine(models.Model):
    _name = "purchase.reorder.line"
    _description = "Purchase Reorder Line"

    product_id = fields.Many2one("product.product", string="Product")
    on_hand = fields.Float(string="On Hand", digits='Product Unit')
    committed = fields.Float(string="Committed", digits='Product Unit')
    on_order = fields.Float(string="On Order", digits='Product Unit')
    available = fields.Float(string="Available", digits='Product Unit')
    minimum = fields.Float(string="Minimum", digits='Product Unit')
    maximum = fields.Float(string="Maximum", digits='Product Unit')
    multiple = fields.Float(string="Multiple", digits='Product Unit')
    suggested_qty = fields.Float(string="Reorder Qty", digits='Product Unit')
    supplier_id = fields.Many2one(
        "res.partner",
        string="Supplier",
        domain="['|', ('supplier_rank', '>', 0), ('customer_rank', '=', 0), " "('is_company', '=', True)]",
    )
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order")

    def create_purchase_order(self, supplier):
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": supplier.id,
                "origin": "Purchase Reorder",
                "date_order": fields.Datetime.now(),
                "state": "draft",
            }
        )

        _log.info(
            f"create_purchase_order - created new purchase order: {purchase_order.display_name}, "
            f"id: {purchase_order.id}"
        )

        # Call required onchange methods.
        purchase_order.onchange_partner_id()
        return purchase_order

    def create_purchase_order_line(self, purchase_order, line):
        purchase_order_line = self.env["purchase.order.line"].create(
            {
                "order_id": purchase_order.id,
                "name": line.product_id.name,
                "product_qty": line.suggested_qty,
                "product_uom_id": line.product_id.uom_id.id,
                "product_id": line.product_id.id,
                "price_unit": line.product_id._select_seller(
                    partner_id=line.supplier_id, quantity=line.suggested_qty
                ).price,
                "state": "draft",
                "date_planned": fields.Date.context_today(self),
                "partner_id": line.supplier_id.id,
            }
        )
        _log.info(
            f"create_purchase_order_line - created purchase order line: {purchase_order_line.id}, "
            f"product: {purchase_order_line.product_id.display_name}"
        )
        purchase_order_line.onchange_product_id()
        purchase_order_line.product_qty = line.suggested_qty

    def action_purchase_order(self):
        for record in self:
            if not record.supplier_id:
                raise UserError("You must have a supplier for every selected record")

        suppliers = list(set([x.supplier_id for x in self.filtered(lambda x: not x.purchase_order_id)]))
        for i in range(0, len(suppliers)):
            supplier = suppliers[i]
            lines = self.filtered(lambda x: x.supplier_id.id == supplier.id and not x.purchase_order_id)
            purchase_order = self.create_purchase_order(supplier)
            print('purchase_order===', purchase_order)
            for line in lines:
                self.create_purchase_order_line(purchase_order, line)
                line.write({"purchase_order_id": purchase_order.id})

            i += 1

        return

    def run_purchase_reorder_create(self):
        # Purge all existing.
        self.search([]).unlink()

        suggested_qty_precision = self.env["decimal.precision"].precision_get("Product Unit")

        products = self.env["product.product"].search([])
        for product in products:
            outgoing_moves = self.env["stock.move"].search(
                [
                    ("product_id", "=", product.id),
                    ("state", "not in", ("done", "cancel")),
                    ("location_dest_id.usage", "=", "customer"),
                ]
            )
            outgoing_qty = sum([x.product_qty for x in outgoing_moves])
            available = product.qty_available - outgoing_qty
            reorder_rule = self.env["stock.warehouse.orderpoint"].search(
                [
                    ("product_id", "=", product.id),
                    ("trigger", "=", "auto"),
                    ("warehouse_id", "=", self.env.company.default_warehouse.id),
                ],
                limit=1,
            )
            min_quantity = reorder_rule.product_min_qty if reorder_rule else 0.0
            if available < min_quantity:
                create_dict = {
                    "product_id": product.id,
                    "on_hand": product.qty_available,
                    "committed": outgoing_qty,
                    "on_order": product.incoming_qty,
                    "available": available,
                }
                supplier = self.env["product.supplierinfo"].search(
                    [("product_tmpl_id", "=", product.product_tmpl_id.id)],
                    order="sequence, min_qty desc, price",
                    limit=1,
                )
                if supplier:
                    create_dict["supplier_id"] = supplier.partner_id.id

                if reorder_rule:
                    create_dict["minimum"] = reorder_rule.product_min_qty
                    create_dict["maximum"] = reorder_rule.product_max_qty
                    # create_dict["multiple"] = 1
                    if reorder_rule.supplier_id:
                        create_dict["supplier_id"] = reorder_rule.supplier_id.id

                    if reorder_rule.product_max_qty:
                        qty_to_order = reorder_rule.product_max_qty - (available + product.incoming_qty)
                    else:
                        qty_to_order = 0 - (
                            available + product.incoming_qty if available + product.incoming_qty > 0.0 else 0.0
                        )
                    if qty_to_order > 0:
                        number_of_multiples = max(int(qty_to_order / 1), 1)
                        qty_to_order = number_of_multiples * 1
                else:
                    qty_to_order = 0 - (
                        available + product.incoming_qty if available + product.incoming_qty < 0.0 else 0.0
                    )

                # Don't create an record if qty_to_order <= 0
                if float_compare(qty_to_order, 0.0, precision_digits=suggested_qty_precision) < 1:
                    continue

                create_dict["suggested_qty"] = qty_to_order if qty_to_order > 0 else 0

                self.create(create_dict)

        return
