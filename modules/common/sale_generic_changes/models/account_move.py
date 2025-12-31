# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Move(models.Model):
    _inherit = "account.move"

    @api.depends('line_ids')
    def _get_sale_orders(self):

        sale_model = self.env["sale.order"]
        for move in self:
            if move.move_type != "out_invoice" or not move.line_ids:
                move.sale_orders = False
                continue

            sale_ids = set()
            for move_line in move.line_ids:
                for sale_line in move_line.sale_line_ids:
                    sale_ids.add(sale_line.order_id.id)
            if sale_ids:
                move.sale_orders = sale_model.browse(sale_ids)
            else:
                move.sale_orders = sale_model

    ###########################################################################
    # Fields
    ###########################################################################
    salesperson_account_id = fields.Many2one(
        "res.partner", string="Salesperson ID", readonly=True,
        help="Salesperson of the Customer/Supplier recorded at the time the invoice was created")
    sale_orders = fields.One2many('sale.order', string='Sale Orders', compute='_get_sale_orders', copy=False)
