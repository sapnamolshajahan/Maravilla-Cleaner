# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    is_parts_return = fields.Boolean("Is Part Return?")
    part_lines = fields.One2many('stock.return.part', 'wizard_id', 'Lines')

    ###########################################################################
    # Model methods
    ###########################################################################

    @api.model
    def default_get(self, fields):
        result = super(StockReturnPicking, self).default_get(
            fields)
        if "product_return_moves" in result:
            move_pool = self.env["stock.move"]
            for a_dict in result["product_return_moves"]:
                dict_list = list(a_dict)
                move_id = dict_list[2]["move_id"]
                if move_id:
                    move = move_pool.browse(move_id)
                    dict_list[2]["quantity"] = 0.0
                    a_dict = tuple(dict_list)

        return result

    def create_returns(self):
        if not self.is_parts_return:
            self._check_return_quantities()

        return super(StockReturnPicking, self).create_returns()

    def _check_return_quantities(self):
        u"""
        :return: Warning if the return quantity is too high
        """
        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        stock_return_picking = self[0]
        for line in stock_return_picking.product_return_moves:
            if (line.move_id and
                    line.move_id.picking_id.picking_type_id.code ==
                    "outgoing"):
                if float_compare(line.quantity,
                                 line.move_id.product_uom_qty,
                                 precision_digits=precision) > 0:
                    raise Warning(
                        ("Product: {p_name} quantity: {qty} exceeds the original shipped quantity: {move_qty}. "
                         "Please reduce the quantity being returned").format(
                            p_name=line.product_id.display_name,
                            qty=line.quantity,
                            move_qty=line.move_id.product_uom_qty))

    def _prepare_move_default_values_for_parts(self, return_line, new_picking):
        move_0 = self.picking_id.move_ids[0]

        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'location_id': self.picking_id.move_ids[0].location_dest_id.id,
            'location_dest_id': self.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': False,
            'procure_method': 'make_to_stock',
            'origin': move_0.origin,
            'partner_id': move_0.partner_id.id,
            'company_id': move_0.company_id.id,
            'name': return_line.move_name or return_line.product_id.name,
            'to_refund': return_line.to_refund,
            'price_unit': return_line.product_id.standard_price
        }
        return vals

    def _create_returns(self):

        if not self.is_parts_return:
            return super(StockReturnPicking, self)._create_returns()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or \
                          self.picking_id.picking_type_id.id

        new_picking = self.picking_id.copy({
            'move_ids': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': "Return of {}".format(self.picking_id.name),
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id})

        new_picking.message_post_with_source('mail.message_origin_link',
                                           render_values={'self': new_picking, 'origin': self.picking_id},
                                           subtype_id=self.env.ref('mail.mt_note').id)

        returned_lines = 0
        for return_line in self.part_lines:
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values_for_parts(return_line, new_picking)
                self.env['stock.move'].create(vals)
        if not returned_lines:
            raise UserError("Please specify at least one non-zero quantity.")

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

    def set_zero_quantity(self):
        for rec in self:
            for move in rec.product_return_moves:
                move.quantity = 0.0

        action = self.env["ir.actions.actions"]._for_xml_id("stock.act_stock_return_picking")
        action['res_id'] = self.id
        return action


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    ###########################################################################
    # - Fields
    ###########################################################################
    move_name = fields.Char(string="Description")


class StockReturnPart(models.TransientModel):
    _name = "stock.return.part"
    _rec_name = 'product_id'
    _description = 'Stock Return Part'

    product_id = fields.Many2one('product.product', string="Product", required=True, ondelete="cascade")
    quantity = fields.Float("Quantity", digits="Product Unit of Measure", required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    wizard_id = fields.Many2one('stock.return.picking', string="Wizard")
    move_name = fields.Char(string="Description")
    to_refund = fields.Boolean(string="To Refund", default=True, help='Trigger to create customer credit note')

    @api.onchange('product_id')
    def onchange_product_id(self):
        vals = {'uom_id': self.product_id.uom_id.id}
        self.update(vals)
