import unittest
from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged
from odoo.addons.hr_accident.report.incident_report_helper import IncidentReportHelper, DetailedIncidentReportHelper


@tagged('hr_accident')
class TestIncidentReportHelper(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env["res.company"].search([], limit=1)

        self.incident_type = self.env["hr.incident.type"].create({
            'name': "Slip"
        })
        self.treatment = self.env["hr.accident.injury.treatment"].create({
            'name': "First Aid"
        })
        self.mechanism = self.env["hr.accident.event.mechanism"].create({
            'name': "Falls"
        })
        self.agency = self.env["hr.accident.event.agency"].create({
            'name': "Agency X"
        })
        self.body_part = self.env["hr.accident.body.part"].create({
            'name': "Arm"
        })
        self.hr_accident = self.env["hr.accident.accident"].create({
            'name': 'ACC001',
            'location': 'Factory Floor',
            'injured_person': 'John Doe',
            'residential_address': '123 Main Street',
            'birth_date': '1985-06-15',
            'sex': 'male',
            'relationship': 'employee',
            'shift': 'day',
            'event_datetime': '2025-01-15 10:00:00',
            'description': 'Slipped on wet floor.',
            'create_date': '2025-01-20 12:00:00',
            'company_id': self.company.id,
            'hr_incident_type_id': self.incident_type.id,
            'hr_accident_injury_treatment_id': self.treatment.id,
            'hr_accident_event_mechanism_id': self.mechanism.id,
            'hr_accident_event_agency_id': self.agency.id,
            'hr_accident_body_part_id': self.body_part.id,
            'hr_accident_employment_period_id': self.env['hr.accident.employment.period'].create({'name': '1 year'}).id,
        })

    def test_append_non_null(self):
        """ensure values are appended correctly. Verifies None does not overwrite existing values."""
        helper = IncidentReportHelper(self.env)
        result = {}

        helper._append_non_null(result, "key1", "value1")
        self.assertEqual(
            result["key1"], "value1",
            "key1 should have the value 'value1' after appending 'value1'."
        )

        helper._append_non_null(result, "key1", None)
        self.assertEqual(
            result["key1"], "value1",
            "key1 should retain the value 'value1' when appending None."
        )

        helper._append_non_null(result, "key1", "new_value")
        self.assertEqual(
            result["key1"], "value1\nnew_value",
            "key1 should concatenate 'new_value' with the existing value, separated by a newline."
        )

    def test_accident_report(self):
        """Validate the `accident` method generates accurate report fields. Ensures report data matches `hr_accident` record"""
        helper = IncidentReportHelper(self.env)
        result = helper.accident(self.hr_accident.id)

        self.assertEqual(
            result["period"], self.hr_accident.hr_accident_employment_period_id.name,
            "The 'period' field should match the employment period name of the accident record."
        )
        self.assertEqual(
            result["incident-type"], "Slip",
            "The 'incident-type' should be 'Slip'."
        )
        self.assertEqual(
            result["treatment"], "First Aid",
            "The 'treatment' should be 'First Aid'."
        )
        self.assertEqual(
            result["mechanism"], "Falls",
            "The 'mechanism' should be 'Falls'."
        )
        self.assertEqual(
            result["agency"], "Agency X",
            "The 'agency' should be 'Agency X'."
        )
        self.assertEqual(
            result["body-part"], "Arm",
            "The 'body-part' should be 'Arm'."
        )
        self.assertEqual(
            result["company"], self.company.name,
            "The 'company' should match the name of the company."
        )

    def test_detailed_accident_report(self):
        """Test `accident` in `DetailedIncidentReportHelper` for default values. Confirms fields are
        initialized correctly."""
        helper = DetailedIncidentReportHelper(self.env)
        result = helper.accident(self.hr_accident.id)

        self.assertEqual(
            result['analysis'], "",
            "The 'analysis' field should be empty by default."
        )
        self.assertEqual(
            result['seriousness'], "",
            "The 'seriousness' field should be empty by default."
        )
        self.assertEqual(
            result['future_probability'], "",
            "The 'future_probability' field should be empty by default."
        )
        self.assertEqual(
            result['actioned_person'], "",
            "The 'actioned_person' field should be empty by default."
        )
        self.assertEqual(
            result['assiting_attendee'], "",
            "The 'assiting_attendee' field should be empty by default."
        )
        self.assertEqual(
            result['medical_entity'], "",
            "The 'medical_entity' field should be empty by default."
        )
        self.assertEqual(
            result['internal_investigator'], "",
            "The 'internal_investigator' field should be empty by default."
        )
        self.assertEqual(
            result['worksafe_advised'], "no",
            "The 'worksafe_advised' field should be 'no' by default."
        )
        self.assertEqual(
            result['investigation_date'], "",
            "The 'investigation_date' field should be empty by default."
        )
