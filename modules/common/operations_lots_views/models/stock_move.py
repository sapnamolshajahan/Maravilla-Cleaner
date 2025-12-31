# -*- coding: utf-8 -*-
from odoo import models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_show_lot_quantities(self):
        self.ensure_one()
        view = self.env.ref('operations_lots_views.stock_quant_picking_tree')
        return {
            'name': _('Lots Available'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            "view_type": "form",
            'res_model': 'stock.quant',
            'view_id': view.id,
            'target': 'new',
            "domain": [('location_id.usage', '=', 'internal'),
                       ('product_id', '=', self.product_id.id),
                       ('location_id', '=', self.location_id.id)
                       ],
            'res_id': self.id,
        }
