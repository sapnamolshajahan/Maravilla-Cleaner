# -*- coding: utf-8 -*-
from odoo import fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    def _compute_eship_enabled(self):
        for picking in self:
            if picking.carrier_id.delivery_type == 'eship':
                picking.is_eship = True
            else:
                picking.is_eship = False

    is_eship = fields.Boolean("Is eShip", compute="_compute_eship_enabled", help="Technical field")
    carrier_shipment = fields.Reference(selection_add=[('eship.carrier.shipment', 'eShip Shipment')], copy=False)
    number_of_packages = fields.Integer(string='Number of Packages', copy=False)
