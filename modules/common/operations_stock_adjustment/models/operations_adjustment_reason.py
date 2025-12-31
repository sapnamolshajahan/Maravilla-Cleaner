from odoo import fields, models


class OperationsAdjustmentReason(models.Model):
    _name = 'operations.adjustment.reason'

    name = fields.Char()
    active = fields.Boolean(default=True)
