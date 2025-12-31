from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_price_unit(self):
        price_unit = super(StockMove, self)._get_price_unit()
        line = self.purchase_line_id
        if line.taxes_id:
            if line.taxes_id[0].price_include:
                return price_unit

        if line.product_uom.id != line.product_id.uom_id.id:
            return price_unit
        return {self.env['stock.lot']: line.price_unit}
