from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class ToolBoxMeeting(models.Model):
    _name = "tool.box.meeting"
    _description = "Tool Box Meeting"

    name = fields.Char(string="Meeting Ref", required=True, copy=False, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    site_location_id = fields.Many2one('res.company', string="Site / Location")
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    time = fields.Datetime(string="Time")
    employee_lead_id = fields.Many2one('hr.employee', string="Lead", required=True)
    attending_employee_ids = fields.Many2many('hr.employee', string="Attending Employees")
    todays_topics = fields.Text(string="Today's Topics")
    hazards_risk = fields.Text(string="Hazards / Risk")
    staff_feedback = fields.Text(string="Staff Feedback / Concerns")
    wrap_up_points = fields.Text(string="Wrap Up and Key Points")
    time_of_closing = fields.Datetime(string="Time of Closing")
    manager_id = fields.Many2one('hr.employee', string="Manager", tracking=True)
    manager_sign = fields.Text(string="Manager Signature")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed'),
    ], string="Status", default='draft', tracking=True)

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tool.box.meeting') or _('New')
        return super(ToolBoxMeeting, self).create(vals_list)

    def action_done(self):
        for rec in self:
            if not rec.manager_sign:
                raise UserError(_("Manager must sign before completing the meeting."))
            rec.state = 'done'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
