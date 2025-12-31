# -*- coding: utf-8 -*-
from odoo import models, fields


class BaseModuleUninstall(models.TransientModel):
    _inherit = "base.module.uninstall"

    ################################################################################
    # Fields
    ################################################################################
    show_all = fields.Boolean(default=True)  # override base' default=False
