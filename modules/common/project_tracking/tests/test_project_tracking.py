# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "project_tracking")
class TestProjectTracking(common.TransactionCase):
    """Class to test crm and project  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.project = self.env.ref('project.project_project_1')
        self.project_2 = self.env.ref('project.project_project_2')
        self.std_milestone = self.env['project.milestone.list'].create({
            'name': 'Test Milestone Name',
        })
        self.project_milestone_1 = self.env['project.milestone'].create({
            'name': 'Initial Milestone Name',
            'project_id': self.project.id
        })
        self.project_milestone_2 = self.env['project.milestone'].create({
            'name': 'Initial Milestone 2',
            'project_id': self.project.id
        })

    def test_project_tracking(self):
        self.assertEqual(self.project_milestone_1.name, 'Initial Milestone Name')
        # Assign a standard milestone
        self.project_milestone_1.std_milestone = self.std_milestone
        self.project_milestone_1.onchange_milestone()
        # Verify the name is updated
        self.assertEqual(
            self.project_milestone_1.name,
            self.std_milestone.name,
        )

    def test_action_view_milestones(self):
        test_project = self.env['project.project'].create({
            'name': 'Test Project',
        })
        self.milestone_1 = self.env['project.milestone'].create({
            'name': 'Milestone 1',
            'project_id': test_project.id,
        })
        self.milestone_2 = self.env['project.milestone'].create({
            'name': 'Milestone 2',
            'project_id': test_project.id,
        })
        action = test_project.action_view_milestones()
        self.assertEqual(action['res_model'], 'project.milestone')
        self.assertEqual(
            action['domain'], [["id", "in", [self.milestone_1.id, self.milestone_2.id]]],
        )
