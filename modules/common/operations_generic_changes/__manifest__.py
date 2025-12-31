# -*- coding: utf-8 -*-
{
    "name": "Operations Generic Changes",
    "version": "19.0.1.0.0",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "category": "Operations",
    "description": """
General View Changes
====================
This module changes standard views to make more usable in a warehouse environment. Plus some logic
from deprecated stock_calculation module that is used
""",
    "depends": [
        "delivery",
        "base_generic_changes",
        "stock_account",
        "account",
        "uom",
    ],
    "data": [
        "views/account_move.xml",
        "views/location.xml",
        "views/picking_view.xml",
        "views/stock_view.xml",
        "views/product.xml",
        "wizard/stock_return_picking_view.xml",
        "security/permissions.xml"
    ],
    "active": False,
    "installable": True,
}
