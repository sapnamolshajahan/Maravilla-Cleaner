# -*- coding: utf-8 -*-
import logging

import pytz

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class GenericCompanyExtension(models.Model):
    _inherit = "res.company"

    @api.model
    def _operations_timezones(self):
        zones = []
        for tz in pytz.all_timezones:
            zones.append((tz, tz))
        return zones

    ###########################################################################
    # Fields
    ###########################################################################
    account_email_address = fields.Char(string="Default email address for accounting")
    operations_timezone = fields.Selection("_operations_timezones", string="Operations Timezone",
                                           default="Pacific/Auckland", required=True,
                                           help="Company's Standard Timezone")
