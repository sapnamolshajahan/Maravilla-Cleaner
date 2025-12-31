# -*- coding: utf-8 -*-
import datetime

from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import fields, models, api


class HrQualificationQualification(models.Model):
    """
    Qualifications.
    """
    _name = "hr.qualification.qualification"
    _description = __doc__

    ###########################################################################
    # Fields
    ###########################################################################
    name = fields.Char(string="Qualification Name", size=256, required=True, help="Name of the Competency.")
    code = fields.Char(string="Code", help="Short Code for Competency")
    active = fields.Boolean(string="Active", default=True, help="Indicates whether the competency is active or not.")


class HrQualificationStatus(models.Model):
    """
    Qualification Status
    """
    _name = "hr.qualification.status"
    _description = __doc__

    name = fields.Char(string="Status Name", size=50, required=True, help="Name of the Competency Status.")
    _sql_constraints = [
        ("unique_status", "unique (name)", "Qualification Status Name must be unique"),
    ]


class HrEmployeeQualification(models.Model):
    """
    Employee Qualifications
    """
    _name = "hr.employee.qualification"
    _description = __doc__
    _order = "date_expiry asc"
    _rec_name = "qualification_id"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    @api.onchange("date_from", "time_period")
    def on_change_time_period_and_start_date(self):
        if self.date_from and self.time_period:
            converted_date = datetime.datetime.strptime(str(self.date_from), "%Y-%m-%d")
            date_after_months = converted_date + relativedelta(months=self.time_period)
            self.date_expiry = date_after_months.strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            self.date_expiry = False

    def _check_expiry_date(self):
        today = fields.Date.context_today(self)

        for record in self:
            expired_date = record.date_expiry

            if expired_date and expired_date < today:
                record.is_expired = True
            else:
                record.is_expired = False

    ###########################################################################
    # Fields
    ###########################################################################
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    qualification_id = fields.Many2one("hr.qualification.qualification", string="Competency", required=True)
    active = fields.Boolean(string="Active", default=True)
    department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department",
                                    readonly=True)
    company_id = fields.Many2one("res.company", related="employee_id.company_id", string="Company", readonly=True)
    status_id = fields.Many2one("hr.qualification.status", string="Status", required=True)
    date_from = fields.Date(string="Date From", required=True)
    notes = fields.Text(string="Notes")
    date_expiry = fields.Date(string="Date Expiry")
    time_period = fields.Integer(string="Time Period (In Months)")
    is_expired = fields.Boolean(compute="_check_expiry_date", string="Expired")
