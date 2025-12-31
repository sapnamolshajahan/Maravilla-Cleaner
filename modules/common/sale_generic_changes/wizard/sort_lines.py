# -*- coding: utf-8 -*-
from odoo import fields, models, api


class SaleOrderSort(models.TransientModel):
    _name = "sale.order.sort"

    sale_order = fields.Many2one(comodel_name='sale.order', string='Sale Order')
    lines = fields.One2many('sale.order.line.sort', 'sale_order_sort', string='Lines')

    def update_sequence(self):
        so_lines_sorted = self.lines.sorted(lambda r: (r.sequence, r.id))
        seq_nr = 10
        for line in so_lines_sorted:
            line.sale_order_line.write({'sequence': seq_nr})
            seq_nr += 10
        return


class SaleOrderLineSort(models.TransientModel):
    _name = 'sale.order.line.sort'

    sale_order_sort = fields.Many2one('sale.order.sort', string='Wizard')
    sequence = fields.Integer(string='Sequence')
    alt_seq = fields.Integer(string='Orig Sequence')
    sale_order_line = fields.Many2one(comodel_name='sale.order.line', string='Sale Order Line')
