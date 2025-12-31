# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AddinReportChart(models.Model):
    _name = "addin.report.chart"
    _inherit = ["mail.thread", 'mail.activity.mixin']

    @api.depends('page_ids')
    def _get_analytic_filter(self):
        for record in self:
            if any(record.page_ids.filtered(lambda x: x.analytic_account)):
                record.has_analytic_filter = True
            else:
                record.has_analytic_filter = False

    name = fields.Char(string="Name")
    company_id = fields.Many2one(string="Company", required=True, comodel_name="res.company",
                                 default=lambda self: self.env.company)
    type = fields.Selection(string="Type",
                            selection=[
                                ("balance-sheet", "Balance Sheet"),
                                ("profit-loss", "Income and Expenditure"),
                                ("cashflow", "CashFlow")
                            ],
                            help="""For opening balance-movement-closing reports, use Income and Expenditure 
                            type even if balance sheet accounts""",
                            required=True)
    account_group_id = fields.Many2one("addin.report.account.group",
                                       required=True, ondelete="cascade",
                                       string="Account Structure")
    page_ids = fields.One2many("addin.report.chart.page", "chart_id", string="Pages")

    include_account_code = fields.Boolean(string='Include Account Code',
                                          help='If checked, will print account code on lines')
    has_analytic_filter = fields.Boolean(string='Has Analytic Filter', compute='_get_analytic_filter',
                                         help='Populates up to report then if yes, different selection logic')

    line_output_level_sequence1 = fields.Selection(string="First Level",
                                                   selection=[
                                                       ("account", "Account")
                                                   ], required=True, default='account')

    @api.onchange("type")
    def onchange_type(self):

        if self.type == "balance-sheet":
            self.line_output_level_sequence1 = "account"

    def _enforce_balance_type(self, vals):
        if "type" in vals and vals["type"] == "balance-sheet":
            vals.update(
                {
                    "line_output_level_sequence1": "account",
                })

    @api.model
    def create(self, vals):
        self._enforce_balance_type(vals)
        return super(AddinReportChart, self).create(vals)

    def write(self, vals):
        self._enforce_balance_type(vals)
        return super(AddinReportChart, self).write(vals)


class AddinChartPage(models.Model):
    """
    Represents a unique sheet/logical break on the output file.
    """
    _name = "addin.report.chart.page"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _order = "chart_id, page_sequence, id"

    name = fields.Char(string="Page Name")
    page_sequence = fields.Integer(string="Sequence",
                                   help="Each unique sequence represents a unique sheet on the XLS file", default=10)
    chart_id = fields.Many2one("addin.report.chart", required=True, string="Chart")
    analytic_account = fields.Many2many('account.analytic.account', string='Analytic Account Filter')


class AddinAccountGroup(models.Model):
    _name = "addin.report.account.group"
    _inherit = ["mail.thread", 'mail.activity.mixin']

    name = fields.Char(string="Header Name", required=True)
    report_name = fields.Many2one(comodel_name='addin.report.name', string='Report Name')
    footer_name = fields.Char(string='Footer Name',
                              help='If specified, this will be printed instead of the Header name')
    print_accounts = fields.Boolean(string='Print Account Detail', default=True)
    parent_id = fields.Many2one('addin.report.account.group', string='Parent Group', index=True,
                                domain="[('report_name','=',report_name)]")
    child_ids = fields.One2many('addin.report.account.group', 'parent_id', string='Child Groups')
    account_tag_ids = fields.Many2many(string='Tags', comodel_name='account.account.tag')
    account_ids = fields.Many2many(string="Accounts", comodel_name="account.account")
    heading = fields.Boolean(string="Print Heading", help="Display Name as Heading on output")
    lines_before = fields.Integer("Lines Before", required=True, default=0, help="Add blank lines before heading")
    subtotal = fields.Boolean(string="Subtotal", help="Enable subtotalling on the group")
    lines_after = fields.Integer("Lines After", required=True, default=0, help="Add blank lines after subtotals")
    sequence = fields.Integer(string="Sequence", default=10)
    signage = fields.Boolean(string="Reverse signage",
                             help="""If checked, calculated value will be reversed, 
                             so a credit value ill be shown as +ve not -ve""")
    opening_balance = fields.Boolean(string='Opening Balance',
                                     help="""If checked, accounts in this group will display 
                                     the opening balance based on the column type""")
    debit_only = fields.Boolean(string='Debit Only',
                                help="""Used for cashflow reporting to separate received 
                                and disbursed for same GL account""")
    credit_only = fields.Boolean(string='Credit Only',
                                 help="""Used for cashflow reporting to separate received 
                                 and disbursed for same GL account""")
    overrride_styling = fields.Many2one("report.xlsx.style", string="Override Styling",
                                        help='Used for account detail rows')
    ratio = fields.Boolean(string='Ratio', help='Tick for this line to be expressed as a ratio of two other lines')
    denomintor_group = fields.Many2one('addin.report.account.group', string='Denominator Group',
                                       help='Bottom of ratio calculation')
    numerator_group = fields.Many2one('addin.report.account.group', string='Numerator Group',
                                      help='Top of ratio calculation')


class AddinReportName(models.Model):
    _name = 'addin.report.name'

    name = fields.Char(string='Name')
