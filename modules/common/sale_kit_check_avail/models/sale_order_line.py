# -*- coding: utf-8 -*-
from odoo import api, models, fields,_
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('display_type', 'product_id')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.product_id:
                bom = self.env["mrp.bom"].sudo()._bom_find(line.product_id)
                bom_default = bom.get(line.product_id)
                if bom and bom_default.type == "phantom":
                    location_ids = line.order_id.warehouse_id.lot_stock_id.id
                    product_model = self.env["product.product"].with_context(location=location_ids)

                    for bom_line in bom_default.bom_line_ids:
                        if not bom_line.product_id.is_storable:
                            continue

                        use_qty = bom_line.product_qty * line.product_uom_qty
                        if not use_qty:
                            continue

                        bom_product = product_model.browse(bom_line.product_id.id)
                        if bom_product.free_qty >= use_qty:
                            continue
                        raise ValidationError(
                            _("Insufficient Inventory : %s requires %d %s %s \nbut warehouse %s has %d %s available.)") %
                            (self.product_id.name, use_qty, bom_product.uom_id.name, bom_product.name,
                             self.order_id.warehouse_id.name, bom_product.free_qty, bom_product.uom_id.name)
                        )

        return super(SaleOrderLine, self)._compute_product_uom_qty()
