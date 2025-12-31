# -*- coding: utf-8 -*-
{
    "name": "Generic Purchase Order Reports",
    "version": "1.0",
    "category": "Purchases",
    "depends": [
        "jasperreports_viaduct",
        "purchase_generic_changes",  # "Purchase Price" decimal precision
        "email_docs",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": """
Purchase Order Reports
======================

Generic reports designed using JasperReports, with support to email or print.

* Purchase Order
* Purchase Quotation
    """,
    "data": [
        "data/email-doc-type.xml",
        "views/partner.xml",
        "views/purchase.xml",
        "reports/reports.xml",
        "data/mail_template.xml",
        "views/res_config.xml",
        "wizards/purchase_order_report.xml",
    ],
    "installable": True,
    "active": False,
}
