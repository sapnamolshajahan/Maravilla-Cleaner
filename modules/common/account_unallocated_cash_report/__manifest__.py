# -*- coding: utf-8 -*-
{
    "name": "Account Unallocated Cash Report",
    "version": "19.0.1.0",
    "category": "Reporting",
    "depends": ["account",
                "account_generic_changes"],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """ Report on Unallocated Items in AR and AP """,
    "data": [
        "security/ir.model.access.csv",
        "wizards/unallocated_cash_report.xml",
    ],
    "installable": True,
    "active": False,
}
