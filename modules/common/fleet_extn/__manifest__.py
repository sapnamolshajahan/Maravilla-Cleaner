# -*- coding: utf-8 -*-
{
    "name": "Fleet Extensions",
    "version": "1.0",
    "category": "",
    "depends": [
        "base_generic_changes",  # "Accounting" decimal-precision
        "fleet",
        "hr",
        "stock",
        "purchase_generic_changes",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """Alter the base fleet package.""",
    "data": [
        "views/purchase.xml",
        "views/fleet.xml",
        "views/stock.xml",
        "security/security.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "active": False,
}
