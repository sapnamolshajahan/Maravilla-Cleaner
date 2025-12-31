# -*- coding: utf-8 -*-
from odoo import fields, models


class HrAccidentCorrectiveActions(models.Model):
    _name = 'hr.accident.corrective.action'
    _description = 'Corrective actions for HR Incidents'

    ###########################################################################
    # Fields
    ###########################################################################

    name = fields.Char(string='Prevention')
    done = fields.Boolean(string='Complete')
    accident_id = fields.Many2one('hr.accident.accident', string='Accident')
