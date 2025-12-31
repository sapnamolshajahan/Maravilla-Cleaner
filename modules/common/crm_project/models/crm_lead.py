# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    def get_line_count(self):
        for record in self:
            if record.account_analytic_lines:
                record.line_count = len(record.account_analytic_lines)
            else:
                record.line_count = 0

    def get_task_count(self):
        for record in self:
            if record.tasks:
                record.task_count = len(record.tasks)
            else:
                record.task_count = 0

    project = fields.Many2one('project.project', string='Project')
    account_analytic = fields.Many2one('account.analytic.account', string='Analytic Account',
                                       related='project.account_id')
    account_analytic_lines = fields.One2many('account.analytic.line', 'crm_lead', string='Timesheet Lines')
    line_count = fields.Integer(string='Timesheets', compute='get_line_count')
    tasks = fields.One2many('project.task', 'crm_lead', string='Tasks')
    task_count = fields.Integer(string='Task Count', compute='get_task_count')

    def action_timesheets(self):
        self.ensure_one()
        if not self.account_analytic_lines:
            return
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "name": "Timesheets",
            "views": [[False, "tree"], [False, "form"]],
            "context": {"create": False},
            "domain": [["id", "in", [x.id for x in self.account_analytic_lines]]],
        }
        if len(self.account_analytic_lines) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = self.account_analytic_lines[0].id

        return action_window

    def action_tasks(self):
        self.ensure_one()
        if not self.tasks:
            return
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "name": "Tasks",
            "views": [[False, "tree"], [False, "form"]],
            "context": {"create": False},
            "domain": [["id", "in", [x.id for x in self.tasks]]],
        }
        if len(self.tasks) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = self.tasks[0].id

        return action_window

    def action_view_project(self):
        self.ensure_one()
        if not self.project:
            return
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "name": "Project",
            "views": [[False, "form"]],
            "context": {"create": False},
            "domain": [("id", "=", self.project.id)],
            "res_id": self.project.id
        }

        return action_window

    @api.model_create_multi
    def create(self, values):
        ignore_crm_lead_create = self.env.context.get("crm_project__ignore_crm_lead_create")

        if ignore_crm_lead_create:
            return super(CRMLead, self).create(values)
        for vals in values:
            if vals.get('type', None) and vals['type'] == 'opportunity' and self.env[
                'ir.config_parameter'].sudo().get_param('crm_project.auto_create_project'):
                if vals.get('partner_id', None):
                    partner = vals['partner_id']
                else:
                    partner = False
                project = self.env['project.project'].create({
                    'name': vals['name'],
                    'partner_id': partner,
                })
                vals['project'] = project.id

        crm_lead = super(CRMLead, self).create(values)

        if crm_lead.project:
            crm_lead.project.write({'crm_lead': crm_lead.id})

        return crm_lead

    def create_project(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "name": "Create Project",
            "views": [[self.env.ref('crm_project.project_project_view_form_simplified_template').id, "form"]],
            "context": {'default_crm_lead': self.id},
            "target": 'new'
        }

    def write(self, values):
        ignore_crm_lead_create = self.env.context.get("crm_project__ignore_crm_lead_create")
        if ignore_crm_lead_create:
            return super(CRMLead, self).write(values)

        if values.get('type') and values['type'] == 'opportunity' and not self.project:
            if values.get('partner_id', None):
                partner = values['partner_id']
            else:
                partner = False
            active_id = self.env.context.get('active_id')
            if active_id:
                crm_lead = self.env['crm.lead'].browse(active_id)
                self.env['project.project'].create({
                    'name': 'Opportunity ' + crm_lead.name,
                    'partner_id': partner,
                })

        res = super(CRMLead, self).write(values)

        for record in self:
            if record.project and not record.project.crm_lead:
                record.project.write({'crm_lead': record.id})

        return res
