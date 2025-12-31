# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "crm_project")
class TestCrmLead(common.TransactionCase):
    """Class to test crm and project  workflow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.crm_lead = self.env.ref('crm.crm_case_1')
        self.crm_lead_2 = self.env.ref('crm.crm_case_2')
        self.project = self.env.ref('project.project_project_1')
        self.project_task = self.env.ref('project.project_1_task_1')
        self.partner = self.env.ref('base.res_partner_12')
        self.employee = self.env.ref('hr.employee_admin')
        self.sale_order = self.env.ref('sale.sale_order_1')
        self.crm_lead.write({
            'project': self.project.id
        })

    def test_crm_lead_actions(self):
        """
         Check different action changes in crm like button functionality to open project order forms and compute
         functionality of field
        """
        # Check analytic line changes
        self.assertEqual(self.crm_lead.line_count, 0)
        self.project.write({
            'crm_lead': self.crm_lead.id
        })
        timesheet = self.env['account.analytic.line'].create({
            'name': 'Test Timesheet',
            'project_id': self.project.id,
            'unit_amount': 2,
            'employee_id': self.employee.id,
        })
        self.assertEqual(timesheet.project_id.id, self.project.id)
        self.assertEqual(timesheet.crm_lead.id, self.project.crm_lead.id)
        self.assertEqual(timesheet.product_uom_id.id, self.env.company.project_time_mode_id.id)
        self.crm_lead.write({
            'account_analytic_lines': [(6,0,timesheet.ids)]
        })
        self.crm_lead.get_line_count()
        self.assertEqual(self.crm_lead.line_count, 1)
        self.crm_lead.write({
            'tasks': [(6,0,self.project_task.ids)]
        })
        self.assertEqual(self.crm_lead.task_count, 1)
        # Timesheet in crm lead view
        self.crm_lead_2.action_timesheets()
        self.assertFalse(self.crm_lead_2.account_analytic_lines)
        result = self.crm_lead.action_timesheets()
        self.assertEqual(result['res_id'], timesheet.id)
        # Tasks in crm lead
        crm_tasks = self.crm_lead.action_tasks()
        self.assertEqual(crm_tasks['res_id'], self.project_task.id)
        # Project in crm lead
        project = self.crm_lead.action_view_project()
        self.assertEqual(project['res_id'], self.project.id)
        self.crm_lead.create_project()
        self.assertEqual(self.project.crm_lead.id, self.crm_lead.id)

    def test_crm_project_setup(self):
        """
        Create,write function project and lead setup
        """
        crm_without_project = self.env['crm.lead'].with_context(crm_project__ignore_crm_lead_create=True).create({
            'name': 'Test Crm'
        })
        self.env["ir.config_parameter"].sudo().set_param('crm_project.auto_create_project', True)
        opportunity = self.env['crm.lead'].create({
            'name': 'Test Opportunity',
            'type': 'opportunity',
            'partner_id': self.partner.id,
        })
        self.assertTrue(opportunity.project)
        self.assertEqual(opportunity.project.name, 'Test Opportunity')
        # write function test cases for project setup
        crm_without_project.write({
            'partner_id': self.partner.id
        })
        self.crm_lead_2.with_context(active_id=self.crm_lead_2.id).write({
            'type': 'opportunity',
            'partner_id': self.partner.id,
        })
        self.assertTrue(self.crm_lead_2.project)
        self.assertEqual(self.crm_lead_2.project.name,'Opportunity Design Software')
        # sale order search in the crm_project module run the test need sale_crm module in the depends also sale_orders field not in project.project
        # self.sale_order.write({
        #     'opportunity_id':  self.crm_lead_2.id
        # })

    def test_project_project_task(self):
        """
        Project and project task create lead functionality check
        """
        project = self.env['project.project'].with_context(tracking_disable=True)
        self.project_template = project.create({
            'name': 'Project TEMPLATE for services',
        })
        new_project = self.env['project.project'].create({
            'name': 'Project 2',
            'allow_timesheets': True,
            'partner_id': self.partner.id,
            'project_template_id': self.project_template.id,
            'alias_id': None,
            'crm_lead': self.crm_lead.id
        })
        self.assertEqual(new_project.id, self.crm_lead.project.id)
        result = new_project.action_view_opportunity()
        self.assertEqual(result['res_id'], self.crm_lead.id)
        self.assertEqual(result['res_model'], 'crm.lead')
        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': new_project.id,
        })
        self.assertEqual(task.crm_lead.id, new_project.crm_lead.id)
