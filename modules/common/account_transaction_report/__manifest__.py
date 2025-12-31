# -*- coding: utf-8 -*-
{
    "name": "Account Transaction Report",
    "version": "19.0.1.0",
    "depends": [
        "account_generic_changes",
        "report_pdf"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": """
    User selects an as at date and XLS file for transactions plus opening/closing balances is produced
    """,
    "website": "https://www.optimysme.co.nz",
    "data": [
        "security/ir_model_access.xml",
        "wizard/account_transaction.xml",
    ],
    "installable": True,
    "active": False,
}
