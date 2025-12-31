# -*- coding: utf-8 -*-
from odoo import models, fields,api,_
from odoo.exceptions import UserError


class PlanningRole(models.Model):
    _inherit = 'planning.role'

    usage = fields.Selection(string='Usage', selection=[('task', 'Tasks'), ('leave', 'Leave'),
                                                        ('workorder', 'WorkOrder')])
