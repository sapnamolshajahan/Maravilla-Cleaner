# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

@tagged('common', 'planning_mrp')
class TestHRLeavePlanningSlot(TransactionCase):

    def setUp(self):
        super(TestHRLeavePlanningSlot, self).setUp()

        self.user = self.env['res.users'].create({
            'name': 'Test Employee User',
            'email': 'test@employee.com',
            'image_1920': False,
            'login': 'test@admin',
            'password': 'testadmin',
        })

        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'user_id': self.user.id,
        })

        self.leave_type = self.env['hr.leave.type'].create({
            'name': 'Test Leave Type',
        })

        self.env['hr.leave'].search([
            ('employee_id', '=', self.employee.id)
        ]).unlink()

        self.leave = self.env['hr.leave'].create({
            'employee_id': self.employee.id,
            'holiday_status_id': self.leave_type.id,
            'date_from': datetime(2025, 5, 10, 9, 0, 0),
            'date_to': datetime(2025, 5, 11, 18, 0, 0),
            'request_unit_hours': False,
        })

    def test_get_duration_hour_request(self):
        self.leave.request_unit_hours = True
        self.leave.request_hour_from = 8
        self.leave.request_hour_to = 12
        duration = self.leave._get_durations()
        self.assertEqual(duration[1], 4.0)


    def test_get_leaves_on_public_holiday_default(self):
        result = self.leave._get_leaves_on_public_holiday()

    def test_get_leaves_on_public_holiday_hourly(self):
        self.leave.request_unit_hours = True
        self.leave.request_hour_from = 8
        self.leave.request_hour_to = 12
        result = self.leave._get_leaves_on_public_holiday()
        self.assertFalse(result)

    def test_create_planning_slot(self):
        record = self.leave
        update_dict = {
            'start_datetime': record.date_from,
            'end_datetime': record.date_to,
        }
        record.create_planning_slot(record, update_dict)
        slot = self.env['planning.slot'].search([('res_id', '=', record.id)])
        self.assertTrue(slot)

    def test_get_planning_slot(self):
        self.leave.get_planning_slot()
        # If no slot exists yet, this will be False
        self.assertIn('planning_slot_id', self.leave)


    def test_write_updates_planning_slot(self):
        new_date_to = self.leave.date_to + timedelta(days=1)
        self.leave.write({'date_to': new_date_to})
        self.assertEqual(self.leave.date_to.date(), new_date_to.date())
