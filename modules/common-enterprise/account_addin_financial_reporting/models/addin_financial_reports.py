# -*- coding: utf-8 -*-

import calendar

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from . import financial_report_constants as C


class FinancialReports(models.Model):
    """ Optimysme Financial Report Presets

        Contains saved financial report selections.  Users can specify a report
        and then save the details for future runs.

    """
    _name = 'addin.financial.report'

    @api.model
    def default_get(self, field_names):
        """ Set financial report defaults.

            Defaults user and created timestamp to current.
            Defaults description to created by user..

            Args:

            Returns:
                Standard default dictionary.
        """
        res = super(FinancialReports, self).default_get(field_names)
        res.update(
            {
                "company_id": self.env.company.id,
                "output": C.REPORT_OUTPUT_SELECTION[0][0],
                "range_period_column_value": C.REPORT_RANGE_VALUES[0][0],
                "rounding": "dollars",
            })
        return res

    @api.depends('name', 'output')
    def _compute_display_name(self):
        for record in self:
            company_name = self.env.company.name
            output_label = dict(C.REPORT_OUTPUT_SELECTION).get(record.output, "")
            record.display_name = f"{record.name}/{company_name}/{output_label}" if record.name else ""

    @api.depends("manual_end")
    @api.onchange("manual_end")
    def _date_end(self):
        """
        End date for the report.
        - use the manual (fixed) date if present
        - work out the range end otherwise
        """
        for report in self:
            if report.manual_end:
                report.date_end = report.manual_end
                continue

            #
            # Work out the last day in the range
            #
            local_today_str = fields.Date.context_today(self)
            local_first = fields.Date.from_string(local_today_str).replace(day=1)

            offset = int(report.range_period_column_value)  # expect a +ve value
            if offset:
                local_first = local_first + relativedelta(months=-offset)

            _first_day, last_day = calendar.monthrange(local_first.year, local_first.month)
            local_last = local_first.replace(day=last_day)

            report.date_end = fields.Date.to_string(local_last)

    @api.depends('chart_id')
    def _get_analytic_filter(self):
        for record in self:
            if record.chart_id.has_analytic_filter:
                record.has_analytic_filter = True
            else:
                record.has_analytic_filter = False

    ################################################################################
    # Fields
    ################################################################################
    create_date = fields.Date(string="Created", readonly=True)
    create_uid = fields.Many2one("res.users", string="Created by", readonly=True)

    # Model fields
    name = fields.Char("Report", required=True,
                       help=("The saved name of this report run. This is also used as the report "
                             "title unless a separate title is specified."))
    chart_id = fields.Many2one(comodel_name="addin.report.chart", ondelete="cascade", required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True,
                                 default=lambda self: self.env.company)
    description = fields.Text(string="Description")
    column_ids = fields.One2many("addin.financial.report.column", "report_id",
                                 string="Report columns", copy=True)

    output = fields.Selection(C.REPORT_OUTPUT_SELECTION, string="Output", required=True)
    range_period_column_value = fields.Selection(
        C.REPORT_RANGE_VALUES,
        string="Range End Value", required=True, default=C.REPORT_OUTPUT_SELECTION[0][0],
        help=("This can be used to set up a report that ends relative to today "
              "so \"Period 0\" means end of the current period etc."))
    manual_end = fields.Date("Fixed End Date", help="If set, this represents the (inclusive) cut-off date")
    date_end = fields.Date(string="Report End Date", compute="_date_end", readonly=True)
    rounding = fields.Selection(C.ROUNDING_SELECTION, string="Rounding", required=True)
    styling = fields.Many2one("addin.styling", string="Styling to be applied")
    print_company_name = fields.Boolean(string='Print Company Name', default=True)
    print_report_name = fields.Boolean(string='Print Report Name', default=True)
    print_run_date = fields.Boolean(string='Print Run Date', default=True)
    print_as_at_date = fields.Boolean(string='Print Report As At Date', default=True)
    include_draft = fields.Boolean(string='Include Draft Entries', default=False,
                                   help='If checked, unposted draft journals will be included in the report')
    has_analytic_filter = fields.Boolean(string='Has Analytic Filter', compute='_get_analytic_filter',
                                         help='Populates up to report then if yes, different selection logic')

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name="{} (copy)".format(self.name))
        return super(FinancialReports, self).copy(default)

    def run_report(self):

        wizard = self.env["addin.financial.report.download"].create_wizard(self)
        return {
            "name": wizard._description,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "target": "new",
        }
