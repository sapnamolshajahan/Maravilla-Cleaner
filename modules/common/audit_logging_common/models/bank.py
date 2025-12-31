# -*- coding: utf-8 -*-

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    _excluded_values = []

    @api.model
    def _get_record_name(self, record):
        u"""Required for audit logging"""
        return 'Partner Bank'

    @api.model
    def create(self, values):
        return self.env['audit.logging'].create_with_log(ResPartnerBank, self, values)

    def write(self, values):
        return self.env['audit.logging'].write_with_log(ResPartnerBank, self, values)

    def unlink(self):
        return self.env['audit.logging'].unlink_with_log(ResPartnerBank, self)
