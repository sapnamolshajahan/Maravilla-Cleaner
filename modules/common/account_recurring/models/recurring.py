# -*- coding: utf-8 -*-
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountRecurring(models.Model):
    """
    Periodic Journals
    """
    _name = "account.recurring"

    ################################################################################
    # Fields
    ################################################################################
    name = fields.Char(string="Description", required=True)
    move = fields.Many2one("account.move", string="Source Journal", required=True, ondelete="cascade")
    interval = fields.Selection(
        [
            ("day", "Daily"),
            ("week", "Weekly"),
            ("month", "Monthly")
        ], string="Interval", default="week", required=True)
    frequency = fields.Integer(string='Frequency', default=1)
    monthly_day = fields.Integer("Day of Month")
    monthly_value = fields.Selection(string='Monthly Day Option', selection=[('first', 'First Day of Month'),
                                                                             ('last', 'Last Day of Month')])
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    last_run_date = fields.Date(string='Last Run Date')
    posted = fields.Boolean(string="Post", help="If yes, journal/invoice will be posted")
    active = fields.Boolean(string="Active", default=True)
    lines = fields.One2many("account.recurring.line", "account_recurring", string="Lines")

    @api.model
    def run_recurring(self):
        today = fields.Date.context_today(self)
        recurring_items = self.env["account.recurring"].search(
            [
                "|",
                ("start_date", "=", False),
                ("start_date", "<=", today),
            ])
        for item in recurring_items:

            if item.end_date and item.end_date < today:
                item.write({"active": False})
                continue

            create_record = self.test_run_me(item, today)

            if create_record:
                item.clone_me(item, today)

    def test_run_me(self, item, today):
        if item.interval == "day":
            return True
        if item.interval == "week":
            return self.run_me_weekly(item, today)
        if item.interval == "month":
            return self.run_me_monthly(item, today)
        return False

    def run_me_weekly(self, item, today):
        if not item.frequency:
            frequency = 1
        else:
            frequency = item.frequency

        if not item.last_run_date:
            first_date = item.start_date + relativedelta(days=7 * frequency)
            if first_date <= today:
                return True

        else:
            next_due_date = item.last_run_date + relativedelta(days=7 * frequency)
            if next_due_date <= today:
                return True
        return False

    def run_me_monthly(self, item, today):
        def get_first_day_next_month(date):
            next_month = date + relativedelta(months=1)
            first_day_next_month = next_month.replace(next_month.year, next_month.month, 1)
            return first_day_next_month

        if not item.frequency:
            frequency = 1
        else:
            frequency = item.frequency

        if not item.last_run_date:
            first_date = item.start_date + relativedelta(months=frequency)
            if item.monthly_day:
                if first_date.day < item.monthly_day:
                    first_date = first_date.replace(first_date.year, first_date.month, item.monthly_day)

            elif item.monthly_value:
                if item.monthly_value == 'first':
                    if today.day > 1:
                        first_date = get_first_day_next_month(first_date)
                else:
                    last_day_of_month = (get_first_day_next_month(first_date) - relativedelta(days=1))
                    last_day = last_day_of_month.day
                    first_date = first_date.replace(first_date.year, first_date.month, last_day)

            if first_date <= today:
                return True
        else:
            next_due_date = item.last_run_date + relativedelta(months=frequency)
            if item.monthly_day:
                if next_due_date.day < item.monthly_day:
                    next_due_date = next_due_date.replace(next_due_date.year, next_due_date.month, item.monthly_day)

            elif item.monthly_value:
                if item.monthly_value == 'first':
                    if today.day > 1:
                        next_due_date = get_first_day_next_month(next_due_date)
                else:
                    last_day_of_month = (get_first_day_next_month(next_due_date) - relativedelta(days=1))
                    last_day = last_day_of_month.day
                    next_due_date = next_due_date.replace(next_due_date.year, next_due_date.month, last_day)

            if next_due_date <= today:
                return True
        return False

    def clone_me(self, item, today):

        new_move_id = item.move.copy(
            {
                "date": fields.Date.context_today(self),
                "ref": item.name
            })

        self.env["account.recurring.line"].create(
            {
                "account_recurring": item.id,
                "date": new_move_id.date,
                "move": new_move_id.id,
            })
        item.write({'last_run_date': today})
        if item.posted:
            new_move_id._post(soft=True)

    def toggle_active(self):
        pass


class AccountRecurringLines(models.Model):
    """
    Log of transactions created
    """
    _name = "account.recurring.line"
    _description = __doc__

    ################################################################################
    # Fields
    ################################################################################
    account_recurring = fields.Many2one("account.recurring", string="Recurring Source",
                                        required=True, ondelete="cascade")
    move = fields.Many2one("account.move", string="Invoice/Journal Created", required=True)
    date = fields.Date(string="Journal Date", required=True)
