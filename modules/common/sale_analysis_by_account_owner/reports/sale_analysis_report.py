# -*- coding: utf-8 -*-
import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class SaleAnalysisReport(models.TransientModel):
    _name = 'sale.analysis.report'
    _description = 'Sale Analysis Report'

    report_name = fields.Char(size=64, string='Report Name', readonly=True, default='Sales Analysis Report.xlsx')
    data = fields.Binary(string="Export filename", readonly=True)
    report_type = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly')], 'Report Type',
                                   default='monthly', required=True)
    company_id = fields.Many2one("res.company", "User Company", default=lambda self: self.env.company.id)
    period_start = fields.Date('Date From', required=True)
    period_to = fields.Date('Date To', required=True)
    region = fields.Many2many('crm.team', 'custom_sale_analysis_report_region_rel', 'region', 'id', 'Region')
    sales_rep = fields.Many2many('res.users', 'custom_sale_analysis_report_sales_rep_rel', 'sales_rep', 'id',
                                 'Sales Rep',
                                 domain="[('company_id','=',company_id)]")
    customer = fields.Many2many('res.partner', 'custom_sale_analysis_report_customer_rel', 'customer', 'id', 'Customer',
                                domain="[('customer_rank', '>', 0),('is_company', '=', True)]")
    category = fields.Many2many('product.category', 'custom_sale_analysis_report_category_rel', 'category', 'id',
                                'Category')
    group_by_category = fields.Boolean('Group By Category')

    ##########################################################################################
    # Functions
    ##########################################################################################

    def run_report(self):
        u"""
        Run report and generate file with results
        :param wizard_id: task.queue object ID
        """

        if self.report_type == "monthly":
            if self.group_by_category:
                report = "sale.analysis.report.categorygroup"
            else:
                report = "sale.analysis.report.nogroup"
        else:
            if self.group_by_category:
                report = "quarterly.sale.analysis.report.categorygroup"
            else:
                report = "quarterly.sale.analysis.report.nogroup"

        _logger.debug("report=" + report)
        self.env[report].with_delay(channel=self.light_job_channel(), description="Sales Analysis Report").get_output(
            self)
