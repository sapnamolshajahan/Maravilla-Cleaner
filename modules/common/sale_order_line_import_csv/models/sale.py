# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class SaleOrderLineImportCsvSaleOrder(models.Model):
    """ Sale order extension for import CSV
        Attributes:
    """
    _inherit = "sale.order"

    def action_import_sale_order_lines(self):
        """ Create the wizard object and return an action to display it.
            Args:
            Returns:
                An action to display the wizard form.
            Raises:
        """
        # self.ensure_one()
        order_id = self.env.context.get('active_id')
        order_item = self.env['sale.order'].search([('id', '=', order_id)])
        if order_item.state != "draft":
            raise UserError("You can only import lines to a sales order that is at Quotation state.")
        vals = {"order_id": order_item.id}
        import_id = self.env["sale.order.line.import"].create(vals)

        return {
            'name': 'Import Sale Order lines from CSV',
            'view_mode': 'form',
            'res_model': 'sale.order.line.import',
            'res_id': import_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            }
