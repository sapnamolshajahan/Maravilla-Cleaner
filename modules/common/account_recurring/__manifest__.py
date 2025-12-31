# -*- coding: utf-8 -*-
{
    "name": "Recurring Journals and Invoices",
    "version": "1.0",
    "summary": "Allows for a journal or invoice to be used to create recurring entries",
    "description": """
        Allows for set up of journals and invoices as recurring transactions
        * daily
        * weekly
        * monthly
        * annually
    """,
    "category": "Accounting",
    "website": "https://optimysme.co.nz",
    "depends": [
        "account",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "data": [
        "data/recurring.xml",
        "views/recurring.xml",
        "security/recurring.xml"
    ],
    "installable": True,
}
