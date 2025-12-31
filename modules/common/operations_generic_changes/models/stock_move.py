# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, api
from odoo.tools import float_is_zero


class StockMove(models.Model):
    """
    Stock move extension.
    """
    _inherit = "stock.move"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    def _get_picking_type_code(self):
        for r in self:
            r.picking_type_code = r.picking_id.picking_type_id.code

    ###########################################################################
    # Fields
    ###########################################################################
    picking_type_code = fields.Char(string="Picking Type Code", readonly=True, compute="_get_picking_type_code")
    price_unit = fields.Float(string="Unit Price", digits="Purchase Price",
                              help=("Technical field used to record the product cost set by the user during a picking "
                                    " confirmation (when average price costing method is used)"))
                            # this adds decimal precision

    ###########################################################################
    # Model methods
    ###########################################################################
    # @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        context = self._context
        if context and "operations_views.stock_return_picking" in context:
            name_dict = context["operations_views.stock_return_picking"]
            default["name"] = name_dict[self.id]
        return super(StockMove, self).copy(default)


    def product_price_update_before_done(self, forced_qty=None):
        """
        override of core so we use the on hand stock not the SVL on hand.
        """
        tmpl_dict = defaultdict(lambda: 0.0)
        lot_tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        std_price_update_lot = {}
        for move in self.filtered(lambda move: move.location_id.usage in (
                'supplier', 'production') and move.product_id.cost_method == 'average'):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            valued_move_lines = move._get_in_move_lines()
            quantity_by_lot = defaultdict(float)
            if forced_qty:
                quantity_by_lot[forced_qty[0]] += forced_qty[1]
            else:
                for valued_move_line in valued_move_lines:
                    quantity_by_lot[valued_move_line.lot_id] += valued_move_line.product_uom_id._compute_quantity(
                        valued_move_line.quantity, move.product_id.uom_id)

            qty_done = move.product_uom._compute_quantity(move.product_qty, move.product_id.uom_id)
            move_cost = move._get_price_unit()
            if float_is_zero(product_tot_qty_available, precision_rounding=rounding) \
                    or float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) \
                    or float_is_zero(product_tot_qty_available + qty_done, precision_rounding=rounding):
                new_std_price = next(iter(move_cost.values()))
            else:
                # Get the standard price
                amount_unit = std_price_update.get(
                    (move.company_id.id, move.product_id.id)) or move.product_id.with_company(
                    move.company_id).standard_price
                qty = forced_qty or qty_done
                # product_tot_qty_available includes this receipt, so we adjust back to work out new average cost
                new_std_price = ((amount_unit * abs(product_tot_qty_available - qty)) + (
                            next(iter(move_cost.values())) * qty)) / (
                                        abs(product_tot_qty_available))

            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_company(move.company_id.id).sudo().with_context(disable_auto_svl=True).write(
                {'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price

            # Update the standard price of the lot
            if not move.product_id.lot_valuated:
                continue
            for lot, qty in quantity_by_lot.items():
                qty_avail = lot.sudo().with_company(move.company_id).quantity_svl + lot_tmpl_dict[lot.id]
                if float_is_zero(qty_avail, precision_rounding=rounding) \
                        or float_is_zero(qty_avail + qty, precision_rounding=rounding):
                    new_std_price = move_cost[lot]
                else:
                    # Get the standard price
                    amount_unit = std_price_update_lot.get((move.company_id.id, lot.id)) or lot.with_company(
                        move.company_id).standard_price
                    new_std_price = ((amount_unit * qty_avail) + (move_cost[lot] * qty)) / (qty_avail + qty)
                lot_tmpl_dict[lot.id] += qty
                lot.with_company(move.company_id.id).with_context(
                    disable_auto_svl=True).sudo().standard_price = new_std_price
                std_price_update_lot[move.company_id.id, lot.id] = new_std_price


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def init(self):
        self.env.cr.execute(f"""  CREATE index if not exists test_idx2 ON stock_move_line (product_id, state, company_id, date)
            """)
    picking_type_code = fields.Char(string='Picking Type Code', related='move_id.picking_type_code', store=True)
