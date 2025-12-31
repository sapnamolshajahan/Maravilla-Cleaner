# -*- coding: utf-8 -*-
{
    "name": "Supplier Pricelist Import",
    "version": "1.0",
    "category": "Purchases",
    "depends": ["product","purchase", "base_generic_changes"],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": """
Import Supplier Pricelists, CSV.
    """,
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "wizards/supplier_pricelist_import.xml",
    ],
    "installable": True,
    "active": False
}
