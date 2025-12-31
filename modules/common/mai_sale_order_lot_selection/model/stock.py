from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.lot', string="Crate", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sale_line_id'):
                sale_line_id = self.env['sale.order.line'].browse(vals['sale_line_id'])
                if sale_line_id and sale_line_id.lot_id:
                    vals.update({'lot_id': sale_line_id.lot_id.id})
        return super(StockMove, self).create(vals_list)

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        for rec in self:
            if rec.sale_line_id and rec.picking_id and rec.lot_id and rec.product_uom_qty == 1:
                for line in rec.picking_id.move_line_ids:
                    line.lot_id = rec.lot_id.id
                    line.quantity = rec.product_uom_qty
        return res
