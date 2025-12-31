# -*- coding: utf-8 -*-
{
    "name": "Financial Reporting",
    "version": "1.0",
    "depends": [
        "account",
        "report_xlsx_styling",
        "queue_job",
        "account_accountant",
        "account_reports",
    ],
    "author": "OptimySME Limited",
    "website": "https://optimysme.nz",
    "category": "Accounting",
    "data": [
        "security/addin_financial_report_security.xml",
        "security/addin-styling.xml",
        "views/addin_financial_reports_view.xml",
        "views/addin-styling.xml",
        "views/chart.xml",
        "wizard/financial_report_download.xml",
        "reports/report_structure.xml",
    ],
    "installable": True,
    "active": False,
}
