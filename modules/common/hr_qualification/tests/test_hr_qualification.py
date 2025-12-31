# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common, tagged

_logger = logging.getLogger(__name__)


@tagged("common", "hr_qualification")
class TestEmployeeQualification(common.TransactionCase):
    """Class to test hr.employee.qualification  workflow for the employee"""

    def setUp(self):
        """
        Extend setUp functionality to create data used in tests
        """
        super().setUp()
        self.employee_id = self.env.ref('hr.employee_admin')
        self.hr_qualification_id = self.env["hr.qualification.qualification"].create({
            "name": "Test Qualification",
            "code": 4879,
        })
        self.qualification_status_id = self.env['hr.qualification.status'].create({
            "name": "Test Status"
        })

    def test_hr_employee_qualification(self):
        """
         Check is_expired field and onchange functionality of date_expiry
        """
        hr_employee_qualification = (
            self.env["hr.employee.qualification"]
            .with_user(self.employee_id.user_id.id)
            .create(
                {
                    "employee_id": self.employee_id.id,
                    "qualification_id": self.hr_qualification_id.id,
                    "department_id": self.employee_id.department_id.id,
                    "company_id": self.employee_id.company_id.id,
                    "status_id": self.qualification_status_id.id,
                    "date_from": "2023-11-02",
                    "date_expiry": fields.Date.today() + relativedelta(days=3),
                    "active": True
                }
            )
        )
        _logger.info("Hr employee qualification created: %s" % hr_employee_qualification)
        # Compute functionality of is_expired
        hr_employee_qualification._check_expiry_date()  # Check expiry date greater than today date
        self.assertFalse(hr_employee_qualification.is_expired)  # is_expired is False
        hr_employee_qualification.write({
            "date_expiry": fields.Date.today() + relativedelta(days=-1)
        })
        hr_employee_qualification._check_expiry_date()  # Check expiry date less than today date
        self.assertTrue(hr_employee_qualification.is_expired)  # is_expired is True
        # Onchange functionality of date_expiry
        hr_employee_qualification.on_change_time_period_and_start_date()
        self.assertFalse(hr_employee_qualification.date_expiry)  # No time_period result is False
        hr_employee_qualification.write({
            "time_period": 5
        })
        hr_employee_qualification.on_change_time_period_and_start_date()
        date_expiry_date_obj = datetime.strptime(str(hr_employee_qualification.date_expiry), "%Y-%m-%d")
        self.assertEqual(date_expiry_date_obj.month, 4)
        # Check toggle active or not
        self.assertTrue(hr_employee_qualification.active)
        self.employee_id.toggle_active()
        self.assertFalse(self.employee_id.active)
        self.assertFalse(hr_employee_qualification.active)
