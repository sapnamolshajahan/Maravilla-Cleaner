# -*- coding: utf-8 -*-
import logging

from odoo.tests import common, tagged


_logger = logging.getLogger(__name__)


@tagged("common", "sale_analysis_by_account_owner")
class TestResPartnerTeam(common.TransactionCase):
    """Class to test res_partner flow"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.sales_team = self.env['crm.team'].create({
            'name': 'Test Sales Team',
        })
        # Creating a parent partner with a team_id
        self.parent_partner = self.env['res.partner'].create({
            'name': 'Parent Partner',
            'company_type': 'person',
            'team_id': self.sales_team.id,
        })
        # Creating a child partner without team_id
        self.child_partner = self.env['res.partner'].create({
            'name': 'Child Partner',
            'company_type': 'person',
            'parent_id': self.parent_partner.id,
        })

    def test_team_id_computation(self):
        self.child_partner._compute_team_id()
        self.assertEqual(self.child_partner.team_id, self.sales_team,
                         "The team_id is not set correctly for the child partner.")

    def test_no_team_id_for_non_person(self):
        # Creating a non-person partner
        non_person_partner = self.env['res.partner'].create({
            'name': 'Non-person Partner',
            'company_type': 'company',  # company type should not inherit team_id
            'parent_id': self.parent_partner.id,
        })
        # Verifying that the team_id is not computed for non-person partners
        self.assertFalse(non_person_partner.team_id, "The team_id should not be set for a non-person partner.")

    def test_no_team_id_when_no_parent(self):
        # Creating a partner without a parent
        partner_without_parent = self.env['res.partner'].create({
            'name': 'Partner without Parent',
            'company_type': 'person',
        })
        # Verifying that the team_id remains unset
        self.assertFalse(partner_without_parent.team_id,
                         "The team_id should not be set for a partner without a parent.")
