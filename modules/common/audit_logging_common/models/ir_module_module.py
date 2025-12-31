# -*- coding: utf-8 -*-
from odoo import api, models


class IRModuleLogging(models.Model):
    _inherit = "ir.module.module"
    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        u"""Required for audit logging"""
        return 'App Module'

    @api.model
    def create(self, values):
        return self.env['audit.logging'].create_with_log(IRModuleLogging, self, values)

    def write(self, values):
        return self.env['audit.logging'].write_with_log(IRModuleLogging, self, values)

    def unlink(self):
        return self.env['audit.logging'].unlink_with_log(IRModuleLogging, self)
