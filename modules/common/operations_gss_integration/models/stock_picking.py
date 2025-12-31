# -*- coding: utf-8 -*-
from odoo import fields, models


class Picking(models.Model):

    _inherit = "stock.picking"

    def _compute_gss_enabled(self):
        for picking in self:
            if picking.carrier_id.delivery_type == 'gss':
                picking.is_gss = True
            else:
                picking.is_gss = False

    is_gss = fields.Boolean("Is GSS", compute="_compute_gss_enabled", help="Technical field")
    carrier_shipment = fields.Reference(selection_add=[('gss.carrier.shipment', 'GSS Shipment')], copy=False)
    number_of_packages = fields.Integer(string='Number of Packages', copy=False)
