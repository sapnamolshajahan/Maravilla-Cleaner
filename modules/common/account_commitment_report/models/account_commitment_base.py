# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountCommitment(models.AbstractModel):
    """
    Base class for Commitment Views.
    """
    _name = "account.commitment.base"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    @api.depends("local_due", "currency_id")
    def _note(self):
        """
        Add a note when no conversion rate and hence no NZD Amount OR commitment is pass its due date
        """
        for r in self:
            if r.local_due == 0 and r.currency_id.name != "NZD":
                r.note = "No conversion rate for {}. Can't calculate NZD Amount".format(r.currency_id.display_name)
            elif r.date_due < fields.Datetime.now():
                r.note = "This commitment is past its due date"
            else:
                r.note = ""

    ###########################################################################
    # Fields
    ###########################################################################
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Supplier", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    reference = fields.Char(string="Reference", size=30, readonly=True)
    tr_date = fields.Date(string="Trans Date", readonly=True)
    date_due = fields.Datetime(string="Date Due", readonly=True)
    total_due = fields.Float(string="Amount", readonly=True, groups="base.group_multi_currency")
    local_due = fields.Float(string="NZD Amount", readonly=True)
    note = fields.Char(string="Note", size=60, compute="_note")

    @classmethod
    def _get_transfer_rate(cls, source):
        """
        Rate would be 0 if rate table has no entries for the currency
        In this case use NULL to nullify NZD Amount field to highlight that the rate is missing
        """
        to_currency = (
            "select rate "
            "from res_currency_rate, res_company "
            "where res_company.id = {source}.company_id "
            "and res_currency_rate.company_id = res_company.id "
            "and res_currency_rate.name <= current_date "
            "and res_currency_rate.currency_id  = res_company.currency_id "
            "order by res_currency_rate.name desc "
            "limit 1").format(source=source)

        from_currency = (
            "select rate "
            "from res_currency_rate "
            "where res_currency_rate.currency_id = {source}.currency_id "
            "and res_currency_rate.name <= current_date "
            "and res_currency_rate.company_id = {source}.company_id "
            "order by res_currency_rate.name desc "
            "limit 1").format(source=source)

        rate = "(({to_currency})/({from_currency}))".format(to_currency=to_currency, from_currency=from_currency)
        return "coalesce ({rate}, 1)".format(rate=rate)

    @classmethod
    def _get_date_due(cls, table, default_key, issued_key):
        """
        Identify date due based on data available
        If no default_key, then check payment_term_id and calculate date based on issued_key + term interval
        Otherwise default to last day of the month following the day of issue

        :param default_key: date_due can be available, check this key first (can be null)
        :param issued_key: key for a day when invoice or purchase order was issued (start date)
        """
        return """case
                when {table}.{default_key} is not null then {table}.{default_key}
                when account_payment_term_line.nb_days != 0
                 then date_trunc ('day', {table}.{issued_key})::DATE + account_payment_term_line.nb_days
                else date_trunc ('month', {table}.{issued_key} + INTERVAL '2 MONTH')::DATE - 1 
                end""".format(table=table, default_key=default_key, issued_key=issued_key)
