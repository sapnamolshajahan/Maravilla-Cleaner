# -*- coding: utf-8 -*-
from collections import namedtuple
from math import floor

from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools import float_round


class StockMove(models.Model):
    _inherit = "stock.move"

    ############################################################################
    # Fields
    ############################################################################
    avail_kit_qty = fields.Float("Available QTY to make up full kits", copy=False)

    ############################################################################
    # Methods
    ############################################################################
    def _ensure_for_full_kits(self):
        # group moves by kit product on sale order line
        sol_kit_groups = {}

        for move in self:
            if move.sale_line_id in sol_kit_groups:
                sol_kit_groups[move.sale_line_id] += move
            else:
                sol_kit_groups[move.sale_line_id] = move

        for sale_line, moves in sol_kit_groups.items():
            kit_qty = sale_line.product_uom_qty
            Detail = namedtuple("Detail", "move factor")
            details = []

            for move in moves:
                soh = self.env['stock.quant']._get_available_quantity(move.product_id, move.location_id)
                factor = soh / (move.product_uom_qty or 1.0)
                details.append(Detail(move=move, factor=factor))

            smallest_factor = list(sorted(details, key=lambda r: r.factor))[0]
            if smallest_factor.factor < 1.0:
                # Reduce kit QTY
                reduced_qty = floor(kit_qty * smallest_factor.factor)
                if not reduced_qty:
                    smallest_factor.move.picking_id.kit_delivery_warning = 'no_kits'
                else:
                    smallest_factor.move.picking_id.kit_delivery_warning = 'some_kits'

                for move in moves:
                    move.avail_kit_qty = reduced_qty * move.bom_line_id.product_qty

            else:
                smallest_factor.move.picking_id.kit_delivery_warning = False
                for move in moves:
                    move.avail_kit_qty = move.product_uom_qty

    def _action_assign(self, force_qty=False):
        kit_moves = self.filtered(lambda r: r.bom_line_id)

        if kit_moves and kit_moves[0].bom_line_id.bom_id.type == 'phantom':
            kit_moves._ensure_for_full_kits()
            standard_moves = self - kit_moves

            if standard_moves:
                super(StockMove, standard_moves)._action_assign()

            super(StockMove, kit_moves.with_context(sale_kit__reserve_full_kits=True))._action_assign()
        else:
            return super(StockMove, self)._action_assign()

    def _update_reserved_quantity(self, need, location_id, quant_ids=None, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        if self.env.context.get('sale_kit__reserve_full_kits'):
            return super(StockMove, self)._update_reserved_quantity(need, location_id,
                                                                    lot_id=lot_id,
                                                                    package_id=package_id, owner_id=owner_id,
                                                                    strict=strict)
        else:
            return super(StockMove, self)._update_reserved_quantity(need, location_id,
                                                                    lot_id=lot_id,
                                                                    package_id=package_id, owner_id=owner_id,
                                                                    strict=strict)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ############################################################################
    # Fields
    ############################################################################
    kit_delivery_warning = fields.Selection([('no_kits', 'No Kits'),
                                             ('some_kits', 'Some Kits')], help="Technical field")

    ############################################################################
    # Methods
    ############################################################################
    def button_validate(self):
        for picking in self:
            if picking.picking_type_id.code != 'outgoing':
                continue

            for move in picking.move_ids:

                if move.bom_line_id and move.bom_line_id.bom_id.type == 'phantom':
                    if  move.quantity % move.bom_line_id.product_qty != 0:
                        raise UserError(
                            'Only fully available kits can be shipped.\n'
                            'Product {name} needs {qty} when sold in a kit.\n'
                            'Quantity that is being dispatched is {dispatched}'.format(
                                name=move.product_id.name,
                                qty=move.bom_line_id.product_qty,
                                dispatched=move.quantity
                            ))

        return super(StockPicking, self).button_validate()

    def _action_done(self):
        for picking in self:
            if not picking.picking_type_id.code == 'outgoing':
                picking.kit_delivery_warning = False
                continue

            kit_components = picking.move_ids.filtered(
                lambda r: r.bom_line_id and r.bom_line_id.bom_id.type == 'phantom')
            non_kit_components = picking.move_ids - kit_components
            if kit_components:
                if kit_components.filtered(lambda r: r.avail_kit_qty == 0.0):
                    if not non_kit_components:  # If only kits on picking, raise error
                        raise UserError("Not enough components to dispatch full kits.")
                    else:
                        break
                sale_lines = kit_components.mapped('sale_line_id')
                for sale_line in sale_lines:
                    this_kit_moves = picking.move_ids.filtered(lambda r: r.sale_line_id == sale_line)
                    move = this_kit_moves[0]
                    # Assumption is only full kits are sold
                    delivered = (move.avail_kit_qty / (
                            move.bom_line_id.product_qty * sale_line.product_uom_qty)) * sale_line.product_uom_qty

                    sale_line.override_qty_delivered = True
                    sale_line.manual_qty_delivered = float_round(delivered, precision_digits=2)

        return super(StockPicking, self)._action_done()

    def create_invoice_lines(self, invoice_type, partner):
        lines = super(StockPicking, self).create_invoice_lines(invoice_type, partner)

        # lines is only NON-kit related products (filtered out by invoice_line_create method in this file)
        # Check if there are any kits in this dispatch:
        if invoice_type == 'sale':
            kit_components = self.move_ids.filtered(
                lambda r: r.bom_line_id and r.bom_line_id.bom_id.type == 'phantom')
            sale_lines = kit_components.mapped('sale_line_id')

            for sale_line in sale_lines:
                lines.append((0, 0, self._prepare_invoice_line_sale_kit(sale_line, partner)))

        return list(filter(lambda r: r[2], lines))

    def invoice_line_create(self, move, invoice_type, partner):
        if move.bom_line_id and move.bom_line_id.bom_id.type == 'phantom':
            return {}
        else:
            return super(StockPicking, self).invoice_line_create(move, invoice_type, partner)

    def _prepare_invoice_line_sale_kit(self, sale_line, partner):
        """
        Preparing values for account.move.line based on sale
        :param sale_line: sale.order.line object
        :return: dict() with values to create a line
        """
        self.ensure_one()
        account = self._get_account_for_sale(sale_line.product_id, partner)
        if sale_line.tax_id.ids:
            tax_ids = [(6, 0, sale_line.tax_id.ids)]
        else:
            tax_ids = False
        return {
            "name": sale_line.name,
            "sequence": sale_line.sequence,
            "account_id": account.id,
            "price_unit": sale_line.price_unit,
            "quantity": sale_line.qty_delivered - sale_line.qty_invoiced,
            "discount": sale_line.discount or 0.0,
            "product_uom_id": sale_line.product_uom.id,
            "product_id": sale_line.product_id.id or False,
            "tax_ids": tax_ids,
            "analytic_account_id": sale_line.order_id.analytic_account_id.id,
            "stock_move_id": False,
            "sale_line_ids": [(4, sale_line.id)],
            "cost_price": sale_line.purchase_price,
        }

    def _prepare_invoice_line_sale_return(self, stock_move, partner):
        """
        Operations auto-invoice links the stock move back to the originating sale order line
        to get the price to be used on the invoice line.

        But in the case of a kit the return is for the component
        so we can set to 0 and include a message in the product description.

        And then let the accountant sort it out.
        """
        values = super(StockPicking, self)._prepare_invoice_line_sale_return(stock_move, partner)

        origin_move = stock_move.origin_returned_move_id
        if origin_move and origin_move.bom_line_id and origin_move.bom_line_id.bom_id.type == 'phantom':
            values.update({
                "name": values.get("name") + '(Return of kit component)',
                'price_unit': 0.0,
                'discount': 0.0,
                'cost_price': stock_move.price_unit
            })

        return values
