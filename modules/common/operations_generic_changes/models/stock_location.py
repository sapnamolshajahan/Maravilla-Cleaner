# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = "stock.location"

    ################################################################################
    # Fields
    ################################################################################

    return_location = fields.Boolean('Is a Return Location?', help='Check this box to allow using this location as a return location.')

