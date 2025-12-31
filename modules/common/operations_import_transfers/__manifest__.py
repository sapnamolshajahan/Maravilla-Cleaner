# -*- coding: utf-8 -*-

{
    "name": "Import CSV Internal Stock Moves",
    "version": "1.0",
    "depends": [
        "stock",
    ],
    'external_dependencies': {
        'python': ['openpyxl']
    },
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "category": "Inventory Control",
    "description": "Create internal moves using CSV files",
    "data": [
        "security/ir.model.access.csv",
        "wizard/import_transfer_csv.xml",
    ],
    "installable": True,
    "active": False,
}
