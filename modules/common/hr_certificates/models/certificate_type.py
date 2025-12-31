# -*- coding: utf-8 -*-
from odoo import models, fields

class CertificateType(models.Model):
    _name = 'hr.certificate.type'
    _description = 'Certificate Type'
    _order = 'name'

    name = fields.Char(string='Certificate Type', required=True, store=True)
