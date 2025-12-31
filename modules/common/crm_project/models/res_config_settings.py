# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_create_project = fields.Boolean(string='Auto Create Project',
                                         config_parameter='crm_project.auto_create_project',
                                         help='Check this field for creating a new project when a new opportunity is generated')
