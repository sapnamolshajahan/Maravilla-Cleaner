# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    ################################################################################
    # Fields
    ###############################################################################
    delay = fields.Integer(string="Supplier Delay (Days)", default=30)
