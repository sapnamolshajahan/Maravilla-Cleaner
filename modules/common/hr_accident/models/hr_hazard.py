from odoo import fields, models


class HrAccidentEmploymentPeriod(models.Model):
    _inherit = "hr.hazard"

    hr_accident_ids = fields.Many2many("hr.accident.accident", string="Incidents")