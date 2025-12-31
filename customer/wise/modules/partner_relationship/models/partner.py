# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    relationships = fields.One2many("partner.relationship", "partner", "Relationships")


