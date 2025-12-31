# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api

_log = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    ###########################################################################
    # Fields
    ###########################################################################
    allowed_mimetypes = fields.Char(string='Allowed mimetypes')
