# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ################################################################################
    # Fields
    ################################################################################
    qualifications = fields.One2many("hr.employee.qualification", "employee_id", string="Competencies")

    def action_archive(self):
        res = super().action_archive()
        for empl in self:
            #  When making employee inactive, make all qualifications inactive but not other way round
            if not empl.active:
                empl.qualifications.write({"active": False})

        return res
