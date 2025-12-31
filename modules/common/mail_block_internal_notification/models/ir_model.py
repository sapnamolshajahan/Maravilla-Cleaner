# -*- coding: utf-8 -*-
from odoo import models, api, fields


class IRModel(models.Model):
    _inherit = 'ir.model'

    block_internal_notification = fields.Boolean(string='Block Internal Notification')

