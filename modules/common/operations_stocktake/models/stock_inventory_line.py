# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class InventoryLine(models.Model):
    _name = "stock.inventory.line"
    _description = "Inventory Line"
    _order = "product_id, inventory_id, location_id, prod_lot_id"

    @api.model
    def _domain_location_id(self):
        if self.env.context.get('active_model') == 'stock.inventory':
            inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
            if inventory.exists() and inventory.location_ids:
                return ("[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit']), "
                        "('id', 'child_of', %s)]") % inventory.location_ids.ids
        return "[('company_id', '=', company_id), ('usage', 'in', ['internal', 'transit'])]"

    @api.model
    def _domain_product_id(self):
        if self.env.context.get('active_model') == 'stock.inventory':
            inventory = self.env['stock.inventory'].browse(self.env.context.get('active_id'))
            if inventory.exists() and len(inventory.product_ids) > 1:
                return ("[('type', '=', 'product'), '|', ('company_id', '=', False), "
                        "('company_id', '=', company_id), ('id', 'in', %s)]") % inventory.product_ids.ids
        return "[('type', '=', 'product'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"

    is_editable = fields.Boolean(help="Technical field to restrict editing.", default=True)
    inventory_id = fields.Many2one('stock.inventory', 'Inventory', check_company=True, index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Owner', check_company=True)
    product_id = fields.Many2one('product.product', 'Product', check_company=True,
                                 domain=lambda self: self._domain_product_id(), index=True, required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True, readonly=True)
    product_qty = fields.Float("Counted Quantity", digits="Product Unit of Measure", default=0)
    categ_id = fields.Many2one(related='product_id.categ_id', store=True)
    location_id = fields.Many2one('stock.location', 'Location', check_company=True,
                                  domain=lambda self: self._domain_location_id(), index=True, required=True)
    package_id = fields.Many2one('stock.package', 'Pack', index=True, check_company=True,
                                 domain="[('location_id', '=', location_id)]")
    prod_lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number', check_company=True,
                                  domain="[('product_id','=',product_id), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', 'Company', related='inventory_id.company_id', index=True, store=True)
    state = fields.Selection(string='Status', related='inventory_id.state')
    theoretical_qty = fields.Float('Expected Quantity', digits='Product Unit of Measure', readonly=True)
    difference_qty = fields.Float('Difference', compute='_compute_difference',
                                  help="Indicates the gap between the product's expected quantity and its newest quantity.",
                                  readonly=True, digits='Product Unit of Measure')
    inventory_date = fields.Datetime('Inventory Date', readonly=True, default=fields.Datetime.now,
                                     help="Last date at which the On Hand Quantity has been computed.")
    product_tracking = fields.Selection(string='Tracking', related='product_id.tracking', readonly=True)
    stock_moves = fields.One2many('stock.move', 'inventory_line', string='Stock Moves')
    moves_done = fields.Boolean("Moves Done", help="If the moves associated with the line have state='done'")

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_difference(self):
        for line in self:
            line.difference_qty = line.product_qty - line.theoretical_qty

    @api.onchange('product_id', 'location_id', 'product_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def _onchange_quantity_context(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
        if self.product_id and self.location_id:
            theoretical_qty = self.product_id.with_context(
                location=self.location_id.id,
                lot=self.prod_lot_id,
                package=self.package_id).qty_available

        else:
            theoretical_qty = 0
        # Sanity check on the lot.
        if self.prod_lot_id:
            if self.product_id.tracking == 'none' or self.product_id != self.prod_lot_id.product_id:
                self.prod_lot_id = False

        if self.prod_lot_id and self.product_id.tracking == 'serial':
            # We force `product_qty` to 1 for SN tracked product because it's
            # the only relevant value aside 0 for this kind of product.
            self.product_qty = 1
        elif self.product_id and float_compare(self.product_qty, self.theoretical_qty,
                                               precision_rounding=self.product_uom_id.rounding) == 0:
            # We update `product_qty` only if it equals to `theoretical_qty` to
            # avoid to reset quantity when user manually set it.
            self.product_qty = theoretical_qty
        self.theoretical_qty = theoretical_qty

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'theoretical_qty' not in values:
                product = self.env['product.product'].browse(values['product_id'])
                theoretical_qty = product.with_context(
                    location=values['location_id'],
                    lot=values.get('prod_lot_id'),
                    package=values.get('package_id')).qty_available
                values['theoretical_qty'] = theoretical_qty
            if 'product_id' in values and 'product_uom_id' not in values:
                values['product_uom_id'] = self.env['product.product'].browse(values['product_id']).uom_id.id
        res = super(InventoryLine, self).create(vals_list)
        res._check_no_duplicate_line()
        return res

    def write(self, vals):
        res = super(InventoryLine, self).write(vals)
        self._check_no_duplicate_line()
        for line in self:
            if line.stock_moves and abs(line.stock_moves[0].product_uom_qty) != abs(line.difference_qty):
                line.stock_moves.write({'state': 'draft'})
                line.stock_moves.unlink()
                line._generate_moves()

        return res

    def unlink(self):
        for record in self:
            record.stock_moves.write({'state': 'draft'})
            record.stock_moves.unlink()
        return super(InventoryLine, self).unlink()

    def _check_no_duplicate_line(self):
        for line in self:
            domain = [
                ('id', '!=', line.id),
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.location_id.id),
                ('partner_id', '=', line.partner_id.id),
                ('package_id', '=', line.package_id.id),
                ('prod_lot_id', '=', line.prod_lot_id.id),
                ('inventory_id', '=', line.inventory_id.id)]
            existings = self.search_count(domain)
            if existings:
                e = """ There is already one inventory adjustment line for product {product},
                you should rather modify this one instead of creating a new one.
                """.format(product=line.product_id.name)
                self.inventory_id.message_post(body=e)
                raise UserError(e)

    @api.constrains('product_id')
    def _check_product_id(self):
        """ As no quants are created for consumable products, it should not be possible do adjust
        their quantity.
        """
        for line in self:
            if line.product_id.type != 'consu':
                raise ValidationError(_("You can only adjust storable products.") + '\n\n%s -> %s' % (
                line.product_id.display_name, line.product_id.type))

    def move_dict(self, qty, location_id, location_dest_id):
        # if self.inventory_id.location_ids:
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                              ('use_create_lots', '=', False),
                                                              ('use_existing_lots', '=', False)], limit=1)
        if not picking_type:
            raise UserError('No valid operation type found. Set up operation type of internal and for Lot/Serial '
                            '- Both Create New and use Existing set to False ')
        move_dict = {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
            'quantity': qty,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            "inventory_line": self.id,
            'reference': _('INV:') + (self.inventory_id.name or ''),
            "date": self.inventory_id.accounting_date}
        return move_dict

    # TODO handle packages
    def move_line_dict(self, qty, location_id, location_dest_id, lot_id):
        move_line_dict = {
            'date': self.inventory_id.date,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_uom_id.id,
            'company_id': self.inventory_id.company_id.id,
            'state': 'confirmed',
            'lot_id': lot_id.id if lot_id else False,
            'lot_name': lot_id.name if lot_id else False,
            'reference': _('INV:') + (self.inventory_id.name or ''),
        }

        return move_line_dict

    def _get_move_values(self, qty, location_id, location_dest_id, lot_id):
        self.ensure_one()
        move_dict = self.move_dict(qty, location_id, location_dest_id)
        move_line_ids = []
        move_line_dict = self.move_line_dict(qty, location_id, location_dest_id, lot_id)
        move_line_ids.append((0, 0, move_line_dict))
        move_dict['move_line_ids'] = move_line_ids

        return move_dict

    def _get_virtual_location(self):
        return self.product_id.with_company(self.company_id).property_stock_inventory

    def _generate_moves(self):

        vals_list = []
        for line in self:
            if line:
                virtual_location = line._get_virtual_location()
                rounding = line.product_id.uom_id.rounding
                if float_is_zero(line.difference_qty, precision_rounding=rounding):
                    line.moves_done = True
                    continue
                if line.difference_qty > 0:  # found more than expected
                    vals = line._get_move_values(line.difference_qty, virtual_location.id, line.location_id.id,
                                                 line.prod_lot_id)
                else:
                    vals = line._get_move_values(abs(line.difference_qty), line.location_id.id, virtual_location.id,
                                                 line.prod_lot_id)
                vals_list.append(vals)
                self.env['stock.move'].create(vals_list)
        return True

    def action_refresh_quantity(self):
        filtered_lines = self.filtered(lambda l: l.state != 'done')
        for line in filtered_lines:
            if line.outdated:
                quants = self.env['stock.quant']._gather(line.product_id, line.location_id, lot_id=line.prod_lot_id,
                                                         package_id=line.package_id, owner_id=line.partner_id,
                                                         strict=True)
                if quants.exists():
                    quantity = sum(quants.mapped('quantity'))
                    if line.theoretical_qty != quantity:
                        line.theoretical_qty = quantity
                else:
                    line.theoretical_qty = 0
                line.inventory_date = fields.Datetime.now()

    def action_reset_product_qty(self):
        """ Write `product_qty` to zero on the selected records. """
        impacted_lines = self.env['stock.inventory.line']
        for line in self:
            if line.state == 'done':
                continue
            impacted_lines |= line
        impacted_lines.write({'product_qty': 0})
