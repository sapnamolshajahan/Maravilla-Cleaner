# -*- coding: utf-8 -*-
{
    "name": "Purchasing Generic View and Logic Modifications",
    "version": "1.0",
    "depends": [
        "purchase",
        "purchase_stock",
        "uom",
        "mail",
        "account",
        "base_generic_changes",
        "stock",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "category": "Purchase",
    "description": "General Purchasing Changes",
    "data": [
        "security/security.xml",
        "views/res_config_settings.xml",
        "views/partner.xml",
        "views/purchase.xml",
        "views/menus.xml",
        "wizard/purchase_done.xml",
    ],
    "installable": True,
    "active": False,
}
