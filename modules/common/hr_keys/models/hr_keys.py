# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrKeyStatus(models.Model):
    _name = "hr.key.status"
    _description = "Key Status"

    name = fields.Char(string="Status Name", required=True, help="Name of the Key Status.")


class HrKey(models.Model):
    _name = "hr.key"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Key"
    _check_company_auto = True

    ###########################################################################
    # Fields
    ###########################################################################

    def _check_expiry_date(self):
        today = datetime.today()

        for record in self:
            expired_date = record.date_expiry

            if expired_date:
                converted_date = datetime.strptime(str(expired_date), DEFAULT_SERVER_DATE_FORMAT)
                record.is_expired = converted_date < today

            else:
                record.is_expired = False

    name = fields.Many2one("hr.key.description", string="Name", required=True)
    date_allocated = fields.Date(string="Date Allocated")
    notes = fields.Text(string="Notes", required=False)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    partner_id = fields.Many2one("res.partner", string="Employee/Contractor", required=True)
    status_id = fields.Many2one(comodel_name='hr.key.status', string='Status')
    date_from = fields.Date(string="Date From")
    date_expiry = fields.Date(string="Date Expiry")
    is_expired = fields.Boolean(compute='_check_expiry_date', string="Expired")
