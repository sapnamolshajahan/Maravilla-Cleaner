# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    inventory_id = fields.Many2one("stock.inventory", string="Inventory")

