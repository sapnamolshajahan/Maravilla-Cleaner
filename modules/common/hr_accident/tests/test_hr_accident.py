from odoo.tests.common import TransactionCase
from odoo.tests import common, tagged


@tagged('hr_accident')
class TestHrAccidentAccident(TransactionCase):
    def setUp(self):
        super().setUp()
        self.accident_model = self.env['hr.accident.accident']
        self.accident = self.accident_model.create({
            'name': 'ACC001',
            'location': 'Factory Floor',
            'injured_person': 'John Doe',
            'residential_address': '123 Main Street',
            'birth_date': '1985-06-15',
            'sex': 'male',
            'relationship': 'employee',
            'hr_accident_employment_period_id': self.env['hr.accident.employment.period'].create({'name': '1 year'}).id,
            'hr_accident_injury_treatment_id': self.env['hr.accident.injury.treatment'].create({'name': 'First Aid'}).id,
            'hr_incident_type_id': self.env['hr.incident.type'].create({'name': 'Slip'}).id,
            'event_datetime': '2025-01-15 10:00:00',
            'shift': 'day',
            'hr_accident_event_mechanism_id': self.env['hr.accident.event.mechanism'].create({'name': 'Slippery Floor'}).id,
            'hr_accident_event_agency_id': self.env['hr.accident.event.agency'].create({'name': 'Floor Surface'}).id,
            'hr_accident_body_part_id': self.env['hr.accident.body.part'].create({'name': 'Leg'}).id,
            'hr_accident_nature_ids': [(6, 0, [self.env['hr.accident.nature'].create({'name': 'Bruise'}).id])],
            'description': 'Slipped on wet floor.',
        })

    def test_unlink(self):
        """
            Ensures that when the unlink method is called, the state of the accident
            record is updated to 'deleted'.
            """
        self.accident.unlink()
        self.assertEqual(self.accident.state, 'deleted', "The state should be updated to 'deleted'.")

    def test_mark_incident_done(self):
        """
        Ensures that calling mark_incident_done changes the state of the accident
        record to 'done'.
        """
        self.accident.mark_incident_done()
        self.assertEqual(self.accident.state, 'done', "The state should be updated to 'done'.")

    def test_mark_incident_open(self):
        """
            Verifies that the state of the accident record transitions to 'open' when
            mark_incident_open is called, even if the current state is 'done'.
            """
        self.accident.write({'state': 'done'})
        self.accident.mark_incident_open()
        self.assertEqual(self.accident.state, 'open', "The state should be updated to 'open'.")
