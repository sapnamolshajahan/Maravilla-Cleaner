# -*- coding: utf-8 -*-

from odoo import models,fields, tools, api
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def action_view_milestones(self):
        self.ensure_one()
        if not self.milestone_ids:
            milestone = self.env['project.milestone'].create({'project_id': self.id})
            action_window = {
                "type": "ir.actions.act_window",
                "res_model": "project.milestone",
                "name": "Milestone",
                "views": [[False, "form"]],
                "context": {"create": True},
                "domain": [["id", "=", milestone.id]],
            }
            return action_window
        else:
            action_window = {
                "type": "ir.actions.act_window",
                "res_model": "project.milestone",
                "name": "Milestone",
                "views": [[False, "list"], [False, "form"]],
                "context": {"create": True},
                "domain": [["id", "in", [x.id for x in self.milestone_ids]]],
            }
            if len(self.milestone_ids) == 1:
                action_window["views"] = [[False, "form"]]
                action_window["res_id"] = self.milestone_ids[0].id

        return action_window
