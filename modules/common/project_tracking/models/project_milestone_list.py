# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ProjectMilestoneList(models.Model):
    """
    Project Milestone Master List
    """
    _name = "project.milestone.list"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################

    name = fields.Char(string='Description', required=True)


class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    ################################################################################
    # Fields
    ################################################################################

    std_milestone = fields.Many2one("project.milestone.list")

    @api.onchange("std_milestone")
    def onchange_milestone(self):
        self.name = self.std_milestone.name
