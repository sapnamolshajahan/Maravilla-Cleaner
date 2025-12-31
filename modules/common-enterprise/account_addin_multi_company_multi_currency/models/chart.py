# -*- coding: utf-8 -*-

from odoo import fields, models


class AddinReportChart(models.Model):
    _inherit = "addin.report.chart"

    include_coy_name = fields.Boolean(string='Include Company Name', help='If checked, conpmay name will be appended to account name')


class AddinChartPage(models.Model):
    """
    Represents a unique sheet/logical break on the output file.
    """
    _inherit = "addin.report.chart.page"

    company_ids = fields.Many2many(comodel_name="res.company", string='Included Companies')
    all_subsidiaries = fields.Boolean(string="Include Their Child Companies",
                                      help='If ticked, all child companies of the included companies will be included as well')


class AddinAccountGroup(models.Model):
    _inherit = "addin.report.account.group"

    consolidate_multi_company = fields.Boolean(string='Consolidate multi-company by code',
                                               help='If the page using this group has a multi-company filter, only report one line per account for all companies')
