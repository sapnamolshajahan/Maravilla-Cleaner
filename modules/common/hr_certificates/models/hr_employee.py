from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certificate_ids = fields.One2many(
        'hr.certificates',
        'employee_id',
    )
    certificate_count = fields.Integer(
        string="Certificates",
        compute="_compute_certificate_count"
    )

    def _compute_certificate_count(self):
        for rec in self:
            rec.certificate_count = len(rec.certificate_ids)

    def action_open_employee_certificates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Certificates',
            'res_model': 'hr.certificates',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            }
        }
