# -*- coding: utf-8 -*-
from odoo.tools import float_compare

from odoo import models, api, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ###########################################################################
    #  Fields methods
    ###########################################################################

    notes = fields.Text(string="Notes", help='Here for historical purposes. No longer used')
    price_changed = fields.Boolean(string="Price Set")

    discount_original = fields.Float(string="discount (Original)",
                                     help=("This field exists to control behaviour on the form "
                                           "only and is not meant to be saved or stored")
                                     )
    price_unit_original = fields.Float(string="Price Unit (Original)",
                                       help=("This field exists to control behaviour on the form "
                                             "only and is not meant to be saved or stored")
                                       )
    purchase_order = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', copy=False)
    stock_moves = fields.One2many("stock.move", "sale_line_id", string="Stock Moves")
    stock_available = fields.Float(string="Available", help="Technical field, updated until confirmed sale")
    stock_available_all = fields.Float('Available All WH')

    _order = 'order_id, sequence asc, id asc'

    @api.onchange('price_changed')
    def onchange_price_changed(self):
        if self.price_changed:
            self.price_unit_original = self.price_unit
            self.discount_original = self.discount

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            if line.price_changed:
                line.price_unit = line.price_unit_original
        return super(SaleOrderLine, self)._compute_price_unit()

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_discount(self):
        super(SaleOrderLine, self)._compute_discount()
        for line in self:
            if line.price_changed:
                line.discount = line.discount_original


    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        res = super(SaleOrderLine, self)._compute_amount()
        for line in self:
            if line.product_id and self.env.company.sale_line_low_price_warning:
                return self.low_margin_check(line)
            line.price_unit_original = line.price_unit
        return res

    def _update_available_qty(self, product, warehouse):
        available_wh = self.env['stock.quant']._get_available_quantity(
            product, warehouse.view_location_id
        )

        all_locations = self.env['stock.location'].search([('usage', '=', 'internal')])
        available_all = sum(
            self.env['stock.quant']._get_available_quantity(product, loc)
            for loc in all_locations
        )

        self.stock_available = available_wh
        self.stock_available_all = available_all

    @api.onchange('product_id')
    def _onchange_product_id_set_availability(self):
        """Only update stock availability when product changes."""
        if not self.product_id:
            self.stock_available = 0.0
            self.stock_available_all = 0.0
            return

        self._update_available_qty(self.product_id, self.order_id.warehouse_id)

        if not self.env.company.sale_line_exclude_in_avail_stock:
            pass
        else:
            self.stock_available = self.stock_available_all

    @api.onchange('product_uom_qty')
    def _onchange_qty_warning(self):
        if (
                self.env.company.sale_line_low_stock_warning
                and self.product_id
                and self.product_uom_qty > self.stock_available
        ):
            new_message = (
                "You plan to sell {} {} but only {} {} is available in {} warehouse."
            ).format(
                self.product_uom_qty,
                self.product_uom_id.name,
                self.stock_available,
                self.product_id.uom_id.name,
                self.order_id.warehouse_id.name
            )
            return {
                'warning': {
                    'title': "Insufficient stock warning!",
                    'message': new_message,
                }
            }

        return {}

    @api.onchange('product_uom_qty', 'price_unit', 'discount', 'product_id')
    def _onchange_check_margin(self):
        for line in self:
            if line.product_id and self.env.company.sale_line_low_price_warning:
                result = self.low_margin_check(line)
                if result:
                    return result

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id:
                line.stock_available_all, line.stock_available = line._get_stock_available()
        return lines

    def _get_display_price(self):
        if self.price_changed:
            return self.price_unit
        return super(SaleOrderLine, self)._get_display_price()

    def outgoing_moves(self, sale_line, warehouse_ids):
        outgoing_all_moves = self.env['stock.move'].search([
            ('product_id', '=', sale_line.product_id.id),
            ('warehouse_id', 'in', [x.id for x in warehouse_ids]),
            ('created_purchase_line_ids', '=', False),
            ('location_dest_id.usage', '!=', 'internal'),
            ('state', 'not in', ('done', 'cancel'))
        ])
        outgoing_all = sum([x.product_uom_qty for x in outgoing_all_moves])
        outgoing_all_excl_this_line = outgoing_all - sale_line.product_uom_qty if \
            sale_line.order_id.state not in ('draft', 'cancel') else outgoing_all
        return outgoing_all_moves, outgoing_all, outgoing_all_excl_this_line

    def outgoing_wh_moves(self, sale_line):
        outgoing_wh_moves = self.env['stock.move'].search([
            ('product_id', '=', sale_line.product_id.id),
            ('warehouse_id', '=', sale_line.warehouse_id.id),
            ('created_purchase_line_ids', '=', False),
            ('location_dest_id.usage', '!=', 'internal'),
            ('state', 'not in', ('done', 'cancel'))])
        outgoing_wh_qty = sum([x.product_uom_qty for x in outgoing_wh_moves])
        outgoing_wh_qty_excl_this_line = outgoing_wh_qty - sale_line.product_uom_qty if \
            sale_line.order_id.state not in ('draft', 'cancel') else outgoing_wh_qty
        return outgoing_wh_moves, outgoing_wh_qty, outgoing_wh_qty_excl_this_line

    def calculate_stock_values(self, sale_line, warehouse_ids):
        on_hand_all = sale_line.product_id.with_context(warehouse=[x.id for x in warehouse_ids]).free_qty
        # need to calculate outgoing to exclude any indent lines linked to a PO line
        outgoing_all_moves, outgoing_all, outgoing_all_excl_this_line = self.outgoing_moves(sale_line, warehouse_ids)
        available_all = on_hand_all - outgoing_all_excl_this_line

        on_hand_wh = sale_line.product_id.with_context(warehouse=sale_line.warehouse_id.id).free_qty
        outgoing_wh_moves, outgoing_wh_qty, outgoing_wh_qty_excl_this_line = self.outgoing_wh_moves(sale_line)

        available_wh = on_hand_wh - outgoing_wh_qty_excl_this_line

        return available_wh, available_all

    def _get_stock_available(self):
        """
        Get the available stock for the order line plus all stock locations.
        """
        if not self.product_id:
            return 0.0, 0.0

        available_all = 0.0
        available_warehouse = 0.0

        warehouse_ids = self.env["stock.warehouse"].search([("exclude_in_avail_stock", "=", False)])

        if warehouse_ids:
            available_warehouse, available_all = \
                self.calculate_stock_values(self, warehouse_ids)

        return available_all, available_warehouse

    def low_margin_check(self, line):
        """ Check if calculated line price is below cost price. """
        calculated_price = line.price_unit - (line.price_unit * (line.discount / 100))
        prec = self.env['decimal.precision'].precision_get('Product Price')
        if float_compare(calculated_price, line.product_id.standard_price,
                         precision_digits=prec) < 0:
            title = "Low margin warning!"
            message = "Check product {product}".format(product=line.product_id.name)
            return {
                'warning': {
                    'title': title,
                    'message': message,
                }
            }
        return

    def check_low_stock(self):
        new_message = "You plan to sell {} {} but you only have {} {} available in {} warehouse.".format(
            self.product_uom_qty, self.product_uom_id.name, self.stock_available, self.product_id.uom_id.name,
            self.order_id.warehouse_id.name)
        title = "Insufficient stock warning!"
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': new_message,
                'sticky': False,
                'type': 'danger'
            }
        }
