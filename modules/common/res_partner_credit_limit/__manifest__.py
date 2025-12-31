# -*- coding: utf-8 -*-
{
    "name": "Partner Credit Limit",
    "version": "1.0",
    "description": """
Partner Credit Limit
====================

When approving a Sale Order it computes the sum of:

    * The credit the Partner has to paid
    * The amount of Sale Orders aproved but not yet invoiced
    * The invoices that are in draft state
    * The amount of the Sale Order to be approved

The value is compared with the credit limit of the partner. If the value
exceeds the credit limit, the sales order will not be approved.
    """,
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "depends": [
        "account",
        "sale",
        "website_sale"
    ],
    "data": [
        "security/groups.xml",
        "views/partner.xml",
        "wizard/credit_limit_report.xml",
        "security/credit_limit_report.xml"
    ],
    "demo": [
        "data/partner-demo.xml",
    ],
    "installable": True,
}
