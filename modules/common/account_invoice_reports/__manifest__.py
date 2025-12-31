# -*- coding: utf-8 -*-
{
    "name": "Standard Invoice Reports",
    "version": "19.0.1.0.0",
    "category": "Reporting",
    "depends": [
        "account_basic_invoice_reports",
        "operations_generic_changes",  # Ref: account.move:picking_ids
        "sale_generic_changes",  # Ref: account.move:sale_orders
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": """
Standard Invoice Print
======================

* Credit Notes
* Invoices
* Sales Order and Stock support
""",
    "data": [
        "reports/reports.xml",
        "views/invoice.xml",
    ],
    "installable": True,
}
