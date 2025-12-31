# -*- coding: utf-8 -*-

{
    "name": "Purchase re-Order",
    "version": "1.0",
    "category": "Inventory Control",
    "depends": [
        "purchase",
        "stock",
        "base_generic_changes",
        "purchase_generic_changes"
    ],
    "author": "Optimysme Limited",
    "website": "http://www.optimysme.co.nz",
    "description": """
    Re-order logic - runs as scheduled job to flag items with negative availablility and show information
    that a user can then evaluate and create a draft PO.
""",
    "data": [
        "data/purchase_reorder_cron.xml",
        "views/purchase_reorder.xml",
        "views/company.xml",
        "security/security.xml"
    ],
    "installable": True,
    "active": False,
}
