# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockPickingPrimepac(models.Model):
    _inherit = 'stock.picking'

    #######################################################################
    # Default and compute methods
    #######################################################################
    @api.depends('signature')
    def _get_pod_captured(self):
        for picking in self:
            picking.pod_captured = 'yes' if picking.signature else 'no'

    @api.onchange('sign_by')
    def onchange_sign_by(self):
        for picking in self:
            if picking.sign_by:
                picking.sign_date = fields.Date.context_today(picking)

    #######################################################################
    # Fields
    #######################################################################
    signature = fields.Binary(string='Signature')
    sign_date = fields.Date(string='Date Signed')
    sign_by = fields.Char(string='Sign By')

    pod_captured = fields.Selection(
        selection=[('yes', 'Yes'), ('no', 'No')],
        string='POD Captured', store=True,
        compute='_get_pod_captured'
    )

    #######################################################################
    # Model methods
    #######################################################################
    def write(self, values):
        if values.get('signature', None):
            pass

        return super(StockPickingPrimepac, self).write(values)
