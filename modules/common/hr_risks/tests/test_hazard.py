# -*- coding: utf-8 -*-

import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)

@tagged("common","hr_risks")
class TestHrRisk(TransactionCase):

    def setUp(self):
        super(TestHrRisk, self).setUp()

        self.hazard_type = self.env['hr.hazard.type'].create({'name': 'Test Hazard Type'})
        self.company = self.env.company

    def test_create_hr_risk(self):
        """Test the creation of an hr.risk record."""
        hazard = self.env['hr.risk'].create({
            'name': 'Risk-001',
            'hazard_type_id': self.hazard_type.id,
            'hazard_identified': 'Slippery floor',
            'description': 'Floor in warehouse is slippery',
            'go_wrong': 'Employee could fall',
            'how_harmed': 'Injury due to slipping',
            'location': 'workshop',
            'risk_matrix': 'moderate',
            'controls': 'minimise',
            'control_measure': 'Add anti-slip mats',
            'recovery_measure': 'First aid kit available',
            'further_action': 'Inspect floor weekly',
            'notes': 'Ensure area is cleaned regularly',
            'review_date': '2025-01-15',
            'company_id': self.company.id,
        })
        self.assertTrue(hazard.id, "Risk record should be created successfully")
        self.assertEqual(hazard.name, 'Risk-001', "Risk name should match")
        self.assertEqual(hazard.hazard_type_id, self.hazard_type, "Risk type should match")

    def test_onchange_likelihood(self):
        """Test the onchange_likelihood method."""
        hazard = self.env['hr.risk'].create({
            'name': 'Risk-002',
            'hazard_type_id': self.hazard_type.id,
            'hazard_identified': 'Exposed wiring',
            'description': 'Exposed wiring in storage room',
            'go_wrong': 'Employee could get electrocuted',
            'how_harmed': 'Electric shock',
            'risk_matrix': 'unacceptable',
            'location': 'office',
            'controls': 'eliminate',
            'control_measure': 'Fix wiring immediately',
            'recovery_measure': 'Ensure circuit breaker is functional',
            'further_action': 'Conduct regular inspections',
            'notes': 'Check electrical fittings quarterly',
            'review_date': '2025-02-01',
            'company_id': self.company.id,
        })

        hazard.consequence = 'major'
        hazard.likelihood = 'possible'
        onchange_result = hazard.onchange_likelihood()
        if onchange_result and 'value' in onchange_result:
            hazard.write(onchange_result['value'])
        self.assertEqual(hazard.risk_matrix, 'moderate',
                         "Risk matrix should be 'moderate' for given consequence and likelihood")

        hazard.consequence = 'catastrophic'
        hazard.likelihood = 'almost_certain'
        onchange_result = hazard.onchange_likelihood()
        if onchange_result and 'value' in onchange_result:
            hazard.write(onchange_result['value'])
        self.assertEqual(hazard.risk_matrix, 'unacceptable',
                         "Risk matrix should be 'unacceptable' for given consequence and likelihood")

    def test_get_hazard_report(self):
        """Test the get_hazard_report method."""
        hazard = self.env['hr.risk'].create({
            'name': 'Risk-003',
            'hazard_type_id': self.hazard_type.id,
            'hazard_identified': 'Heavy lifting',
            'risk_matrix': 'high',
            'description': 'Frequent heavy lifting in warehouse',
            'go_wrong': 'Employee could strain back',
            'how_harmed': 'Back injury',
            'location': 'yard',
            'controls': 'minimise',
            'control_measure': 'Provide training on proper lifting techniques',
            'recovery_measure': 'Have medical support available',
            'further_action': 'Procure lifting equipment',
            'notes': 'Monitor employee health',
            'review_date': '2025-03-01',
            'company_id': self.company.id,
        })

        report = hazard.get_hazard_report()
        self.assertTrue(report, "Risk report reference should be returned")
        self.assertEqual(report.name, 'Risk register Report', "The returned report name should match the expected value")
