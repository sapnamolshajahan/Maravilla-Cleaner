from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one('stock.lot', 'Lot', copy=False)

    def _prepare_procurement_values(self):
        res = super(SaleOrderLine, self)._prepare_procurement_values()
        res['lot_id'] = self.lot_id.id
        return res
