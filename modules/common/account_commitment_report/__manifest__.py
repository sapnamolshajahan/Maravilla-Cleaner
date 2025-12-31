# -*- coding: utf-8 -*-
{
    "name": "Cashflow Commitments Report",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "author": "Solnet Solutions Ltd",
    "website": "http://solnet.co.nz",
    "depends": [
        "account_generic_changes",
        "base_generic_changes",
        "purchase",
        "purchase_generic_changes",
    ],
    "description":
        """
Committment Views
=================
Create views to view and explore future cashflow commitments by currency. The future cashflow commitments are a
combination of existing unpaid supplier invoices and existing confirmed purchase orders that have not been paid.
        """,
    "data": [
        "security/access.xml",
        "security/rules.xml",
        "views/account_commitment_report.xml",
        "views/account_commitment_report_detailed.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
