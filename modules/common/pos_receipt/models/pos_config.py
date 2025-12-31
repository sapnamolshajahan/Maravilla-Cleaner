# -*- coding: utf-8 -*-
from odoo import models, fields


class POSConfig(models.Model):
    _inherit = "pos.config"

    ################################################################################
    # Fields
    ################################################################################
    pos_receipt_queue = fields.Many2one("pos.queue.escpos", string="POS Receipt Queue")
