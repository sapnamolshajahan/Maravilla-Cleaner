# -*- coding: utf-8 -*-

from odoo import models, fields

class DummyModel(models.Model):
    _name = 'dummy.model'
    _description = 'Dummy model for RemoteProxyClient tests'
    _remote_name = 'res.partner'

    name = fields.Char()
