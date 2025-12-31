# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.depends("picking_ids")
    def count_picking(self):
        for r in self:
            r.picking_count = len(r.picking_ids)

    ###########################################################################
    # Fields
    ###########################################################################
    picking_ids = fields.One2many("stock.picking", "invoice_id", "Pickings")
    picking_count = fields.Integer(string="No. of pickings related", compute="count_picking")

    ###########################################################################
    # Model methods
    ###########################################################################
    def action_view_stock_picking(self):
        """
        This function returns an action that display existing pickings of given invoice (self).
        It can either be a in a list or in a form view, if there is only one delivery order to show.
        """
        picking_ids = self.mapped("picking_ids")

        result = {
            "name": 'Picking',
            "type": 'ir.actions.act_window',
            'views': [(self.env.ref('operations_generic_changes.stock_picking_tree').id, 'tree'),
                      (self.env.ref('stock.view_picking_form').id, 'form')],
            "target": 'new',
            "context": self.env.context,
            "res_model": 'stock.picking',
        }

        # Go to sale orders tree view
        if len(picking_ids) > 1:
            result["domain"] = "[('id', 'in', %s)]" % picking_ids.ids

        # Go to sale order form
        elif len(picking_ids) == 1:
            result["views"] = [(self.env.ref('stock.view_picking_form').id, "form")]
            result["res_id"] = picking_ids.ids[0]

        else:
            result = {"type": "ir.actions.act_window_close"}

        return result
