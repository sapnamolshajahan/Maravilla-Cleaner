# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    crm_lead = fields.Many2one('crm.lead', string='Opportunity')
    crm_lead_state = fields.Many2one('crm.stage', string='Opportunity State', related='crm_lead.stage_id')
    crm_won = fields.Boolean(string='Opportunity Won', related='crm_lead_state.is_won')
    project_template_id = fields.Many2one(comodel_name='project.project', string='Project Template',
                                          domain=lambda self: [('active', '!=', False),
                                                               ('company_id', '=', self.env.company.id)])
    template = fields.Boolean(string='Template')

    def action_view_opportunity(self):
        self.ensure_one()
        if not self:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('No opportunities'),
                    'message': _('There are no opportunities in this project'),
                }
            }
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "name": "Opportunity",
            "views": [[False, "form"]],
            "context": {"create": False},
            "domain": [("id", "=", self.crm_lead.id)],
            "res_id": self.crm_lead.id
        }

        return action_window

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_template = vals.get('project_template_id')
            if project_template:
                new_project = self.env['project.project'].browse(project_template).copy()
                vals['template'] = False
                if not vals.get('alias_id'):
                    del vals['alias_id']
                new_project.write(vals)
                crm_lead = self.env['crm.lead'].browse(vals.get('crm_lead'))
                crm_lead.write({
                    'project':new_project.id
                })
                return new_project
        res = super(ProjectProject, self).create(vals_list)
        if res.crm_lead:
            res.crm_lead.write({'project': res.id})
        return res
