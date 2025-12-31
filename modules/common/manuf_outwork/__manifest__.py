# -*- coding: utf-8 -*-
{
    "name": "Manufacturing Outwork",
    "version": "1.0",
    "depends": [
        "base",
        "mrp",
        "stock",
        'product',
        'purchase',
        'purchase_stock',
    ],
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "category": "Utilities",
    "description": """provides concept of outwork using a work centre representing a supplier.
.""",
    "data": [
        "views/mrp_workorder.xml",
        "views/res_config_settings_views.xml"
    ],
    "installable": True
}
