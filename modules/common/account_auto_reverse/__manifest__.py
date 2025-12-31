# -*- coding: utf-8 -*-
{
    "name": "Auto-reverse Journals",
    "version": "1.0",
    "summary": "Extend standard functionality to allow a user to have a reversing journal automatically created",
    "description": """
            Option on journal entry to create a reversing entry without having to use the wizard. Reversing entry will be dated 1st of month following
    """,
    "category": "Accounting",
    "website": "https://www.optimysme.nz",
    "depends": [
        "account",
        "account_generic_changes"
    ],
    "author": "OptimySME Limited",
    "data": [
        "views/account.xml",

    ],
    "demo": [],
    "qweb": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
