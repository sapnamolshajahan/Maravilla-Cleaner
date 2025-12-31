# -*- coding: utf-8 -*-
{
    "name": "Operations - Stocktake",
    "version": "1.0",
    "depends": [
        "stock_account",
        "operations_multibin",
        "mrp",
        "stock",
        "account",
        "queue_job",
    ],
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "category": "Inventory Control",
    "description": """
        Provides stock take functionality for large businesses.
    """,
    "data": [
        "security/stock-inventory.xml",
        "security/record_rules.xml",
        "security/permissions.xml",
        "views/stock_inventory_views.xml",
        "views/menu-roots.xml",
        "views/stocktake_data_entry.xml",
        "wizard/count_sheets.xml",
        "wizard/stocktake_variance.xml",
        "wizard/stocktake_checking.xml",
        "wizard/stocktake_import_count.xml",
    ],
    "installable": True,
    "active": False,
}
