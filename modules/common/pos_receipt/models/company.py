# -*- coding: utf-8 -*-
import base64

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    ################################################################################
    # Compute
    ################################################################################
    def _pos_logo_b64(self):
        for rec in self:
            if rec.pos_logo:
                rec.pos_logo_b64 = base64.b64encode(rec.pos_logo)
            else:
                rec.pos_logo_b64 = None

    ################################################################################
    # Fields
    ################################################################################
    pos_logo = fields.Binary("POS Logo", help="Logo for POS Receipt. Preferably B&W logo, 100px in height")
    pos_logo_b64 = fields.Binary("POS Logo B64 encoded", compute="_pos_logo_b64")
