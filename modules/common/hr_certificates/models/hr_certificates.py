from odoo import models,fields,api, _
from datetime import date


class HrCertificate(models.Model):
    _name = 'hr.certificates'
    _description = 'Employee Certificates'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    certificate_type_id = fields.Many2one('hr.certificate.type', string="Certificate Type", required=True, tracking=True)
    upload = fields.Binary(string="Upload Certificate (PDF)")
    upload_filename = fields.Char(string="Filename")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    notification_date = fields.Date(string="Notification Date")
    responsible_manager_id = fields.Many2one('hr.employee', string="Responsible Manager", tracking=True)
    state = fields.Selection([('draft', 'Draft'),('done', 'Done'),], string="Status", store=True, default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.certificates') or _('New')
        return super().create(vals_list)

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

        # 🔁 CRON JOB FUNCTION

    @api.model
    def _cron_check_certificate_expiry(self):
        today = date.today()
        certificates = self.search([
            ('notification_date', '<=', today),
            ('state', '=', 'draft'),
            ('responsible_manager_id.work_email', '!=', False)
        ])

        mail_template = self.env.ref('hr_certificates.email_template_certificate_expiry', raise_if_not_found=False)
        if not mail_template:
            return  # no template configured

        for cert in certificates:
            mail_template.send_mail(cert.id, force_send=True)

