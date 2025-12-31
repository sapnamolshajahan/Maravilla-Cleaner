# -*- coding: utf-8 -*-
{
    "name": "Partner Statement and Aged Trial Balance Reporting",
    "version": "1.0",
    "category": "Reporting",
    "depends": [
        "account",
        "account_basic_invoice_reports",  # invoice_display_address()
        "email_docs",
        "queue_job",
        "base_generic_changes",
        "account_accountant"
    ],
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "license": "Other proprietary",
    "description": """
Partner Statement of Account and various aging reports
======================================================

This module generates partner statements for printing and email,
using standard Odoo payment and banking.

Bulk Statement Mailout
----------------------
To configure:

    Create email template
        "Applies To" should be "res.partner.statement.email"

    Create email document type
        Technical Settings -> Email -> Document Emailing Type.
        Set report to the correct email statement and template to
        the new template.

    Partner
        Create a partner-statement document email.

TO DO:
    - group by parent - TO CHECK LOGIC
    - for non-NZD detailed and summary ATB check logic is correct and required data printed
""",
    "data": [
        "security/res_partner_reports_security.xml",
        "data/email-templates.xml",  # defines templates used by email-doc-type.xml
        "data/email-doc-type.xml",
        "report/reports.xml",
        "wizard/res_partner_statement.xml",  # this is used by partner_view_extension.xml
        "views/partner_view_extension.xml",
        "views/res_config_settings.xml",
        "wizard/atb_summary_view.xml",
        "wizard/atb_audit.xml",
        "wizard/atb_detail_view.xml",
        "wizard/atb_by_currency_view.xml",
        "wizard/open_invoice.xml",
    ],
    "installable": True,
    "active": False,
}
