import logging

from odoo import models, fields, api,_
_logger = logging.getLogger(__name__)


class XeroInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    xero_invoice_line_id = fields.Char(string="Xero Id", copy=False)
    inclusive = fields.Boolean('Inclusive', default=False, copy=False)
    analytic_account_id = fields.Many2one(string='Analytic Account',
                                       comodel_name='account.analytic.account')
    is_anglo_saxon_line = fields.Boolean(help="Technical field used to retrieve the anglo-saxon lines.")

    @api.model_create_multi
    def create(self, vals_list):
        line = super(XeroInvoiceLine, self).create(vals_list)

        if not line.analytic_account_id:
            line.assign_default_analytic()

        return line

    def assign_default_analytic(self):
        for line in self:
            sale = line.sale_line_ids.mapped('order_id')
            if sale and sale[0].warehouse_id:
                line.analytic_account_id = sale[0].warehouse_id.get_default_analytic_account()
                continue

            purchase = line.purchase_order_id
            if purchase and purchase.picking_type_id:
                line.analytic_account_id = purchase.picking_type_id.warehouse_id.get_default_analytic_account()
                continue
