# -*- coding: utf-8 -*-
{
    "name": "Purchase Order Import",
    "version": "1.0",
    "depends": [
        "purchase",
        "base_generic_changes"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Purchases",
    "description": """ Import purchase order lines from an XLS file, with support for variants. """,
    "data": [
        "wizard/purchase_line_import.xml",
        "wizard/purchase_order_value.xml",
        "security/security.xml"
    ],
    "external_dependencies": {"python": ["openpyxl"]},
    "installable": True,
    "active": False,
}
