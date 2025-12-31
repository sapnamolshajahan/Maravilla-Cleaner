# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    fp_product_id = fields.Many2one("product.product", string="Final Product Variant", compute="_compute_fp_product_id",
                                    store=True,
                                    help="Technical field, it is used to determine which product variant the final product is when MOs are created with bom containing intermediat products")

    @api.depends('product_id', 'origin')
    def _compute_fp_product_id(self):
        for mo in self:
            if mo.product_id.is_intermediate:
                parent_mo = self.search([('name', '=', mo.origin)], limit=1)
                mo.fp_product_id = parent_mo.fp_product_id
            else:
                mo.fp_product_id = mo.product_id

    @api.depends('company_id', 'bom_id', 'product_id', 'product_qty', 'product_uom_id', 'location_src_id')
    def _compute_move_raw_ids(self):
        for production in self:
            if production.state != 'draft' or self.env.context.get('skip_compute_move_raw_ids'):
                continue
            list_move_raw = [Command.link(move.id) for move in
                             production.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
            if not production.bom_id and not production._origin.product_id:
                production.move_raw_ids = list_move_raw

            for move in production.move_raw_ids:
                if move.bom_line_id:
                    if production.bom_id.is_intermediate:
                        if move.bom_line_id.bom_id != production.bom_id or move.bom_line_id._skip_bom_line(
                                production.fp_product_id):
                            production.move_raw_ids = [Command.clear()]
                            break
                    else:
                        if move.bom_line_id.bom_id != production.bom_id or move.bom_line_id._skip_bom_line(
                                production.product_id):
                            production.move_raw_ids = [Command.clear()]
                            break

            if production.bom_id and production.fp_product_id and production.product_qty > 0:
                # keep manual entries
                moves_raw_values = production._get_moves_raw_values()
                move_raw_dict = {move.bom_line_id.id: move for move in
                                 production.move_raw_ids.filtered(lambda m: m.bom_line_id)}
                for move_raw_values in moves_raw_values:
                    if move_raw_values['bom_line_id'] in move_raw_dict:
                        # update existing entries
                        list_move_raw += [
                            Command.update(move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                    else:
                        # add new entries
                        list_move_raw += [Command.create(move_raw_values)]
                production.move_raw_ids = list_move_raw
            else:
                production.move_raw_ids = [Command.delete(move.id) for move in
                                           production.move_raw_ids.filtered(lambda m: m.bom_line_id)]

    def _get_moves_raw_values(self):
        moves = []
        for production in self:
            if not production.bom_id:
                continue

            factor = production.product_uom_id._compute_quantity(production.product_qty,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.fp_product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or \
                        bom_line.product_id.type not in ['consu']:
                    continue
                operation = bom_line.operation_id.id or line_data['parent_line'] and line_data[
                    'parent_line'].operation_id.id
                moves.append(production._get_move_raw_values(
                    bom_line.product_id,
                    line_data['qty'],
                    bom_line.product_uom_id,
                    operation,
                    bom_line
                ))
        return moves

    # def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
    #     """ Warning, any changes done to this method will need to be repeated for consistency in:
    #         - Manually added components, i.e. "default_" values in view
    #         - Moves from a copied MO, i.e. move.create
    #         - Existing moves during backorder creation """
    #     if bom_line and bom_line.bom_id.is_intermediate:
    #         product_id = self.fp_product_id
    #
    #     source_location = self.location_src_id
    #     data = {
    #         'sequence': bom_line.sequence if bom_line else 10,
    #         'name': _('New'),
    #         'date': self.date_start,
    #         'date_deadline': self.date_start,
    #         'bom_line_id': bom_line.id if bom_line else False,
    #         'picking_type_id': self.picking_type_id.id,
    #         'product_id': product_id.id,
    #         'product_uom_qty': product_uom_qty,
    #         'product_uom': product_uom.id,
    #         'location_id': source_location.id,
    #         'location_dest_id': product_id.with_company(self.company_id).property_stock_production.id,
    #         'raw_material_production_id': self.id,
    #         'company_id': self.company_id.id,
    #         'operation_id': operation_id,
    #         'procure_method': 'make_to_stock',
    #         'origin': self._get_origin(),
    #         'state': 'draft',
    #         'warehouse_id': source_location.warehouse_id.id,
    #         'group_id': self.procurement_group_id.id,
    #         'propagate_cancel': self.propagate_cancel,
    #         'manual_consumption': self.env['stock.move']._determine_is_manual_consumption(product_id, self, bom_line),
    #     }
    #     return data
