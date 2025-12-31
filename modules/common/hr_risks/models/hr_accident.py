from odoo import fields, models


class HrAccidentRiskEmploymentPeriod(models.Model):
    _inherit = "hr.accident.accident"

    hr_risk_id = fields.Many2one('hr.risk', string="Risk")
