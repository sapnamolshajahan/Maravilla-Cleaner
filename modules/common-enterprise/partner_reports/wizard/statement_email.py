# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.config import config


class statement_email(models.TransientModel):
    """
    Data holder for Statement Email reports.

    This just holds references to the statement-wizard and partner combinations
    that need to have an email generated.

    A email.doc.type (type="partner-statement-2") with a template referencing this model
    will be used to email the statement to the partner.
    """
    _name = "res.partner.statement.email"
    _description = 'Ar and AP Statement Email'

    ###########################################################################
    # Default and compute methods.
    ###########################################################################
    def _get_config_from_addy(self):
        for record in self:
            record.config_from_address = config.get("email_from", "")

    ###########################################################################
    # Fields
    ###########################################################################
    res_partner_statement_id = fields.Many2one("res.partner.statement", string="Statement")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    config_from_address = fields.Char('Configuration From Address', readonly=True, compute='_get_config_from_addy')
    company_id = fields.Many2one(comodel_name="res.company", string='Company',
                                 default=lambda self: self.env.company)

    @api.model
    def email_doc_report(self):
        """
        Return the report-name to use for Partner Statements.
        Override to provide customer-specific report-names.

        :return: ir.actions.report record
        """
        return self.env.ref("partner_reports.generic_partner_statement_email")
