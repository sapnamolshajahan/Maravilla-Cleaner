# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    crm_lead = fields.Many2one('crm.lead', string='Opportunity')

    @api.model_create_multi
    def create(self, vals_list):
        task = super(ProjectTask, self).create(vals_list)
        if task.project_id.crm_lead:
            task.write({'crm_lead': task.project_id.crm_lead.id})
        return task
