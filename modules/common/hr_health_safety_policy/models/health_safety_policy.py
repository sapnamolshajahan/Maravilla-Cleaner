# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class HrHealthSafetyPolicy(models.Model):
    _name = 'hr.health.safety.policy'
    _description = 'HR Health and Safety Policy'

    name = fields.Char(string='Policy Name', required=True)
    sequence = fields.Char(string='Policy Reference', readonly=True, copy=False)
    start_date = fields.Date(string='Start Date', required=True)
    notification_date = fields.Date(string='Notification Date')
    end_date = fields.Date(string='End Date', required=True)
    responsible_manager_id = fields.Many2one('hr.employee', string='Responsible Manager')
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
    ], string='Status', compute='_compute_status', store=True)
    policy_document = fields.Binary(string='Policy Document')

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence'):
                vals['sequence'] = self.env['ir.sequence'].next_by_code('hr.health.safety.policy') or '/'
        return super(HrHealthSafetyPolicy, self).create(vals_list)

    @api.depends('end_date')
    def _compute_status(self):
        today = date.today()
        for record in self:
            if record.end_date and record.end_date >= today:
                record.status = 'active'
            else:
                record.status = 'expired'

    @api.model
    def cron_send_health_policy_notification(self):
        today = date.today()
        policies = self.search([
            ('notification_date', '<=', today),
            ('status', '=', 'active'),
            ('responsible_manager_id', '!=', False)
        ])
        mail_template = self.env.ref('hr_health_safety_policy.mail_template_health_policy_notification')
        for policy in policies:
            mail_template.send_mail(policy.id, force_send=True)
