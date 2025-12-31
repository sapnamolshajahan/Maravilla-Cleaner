# -*- coding: utf-8 -*-
{
    "name": "Operations - Stock Adjustment",
    "version": "1.0",
    "depends": [
        "stock",
        "stock_account",
        "account",
    ],
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "category": "Inventory Control",
    "description": """
        Operations - Stock Adjustment with Approval
    """,
    "data": [
        "security/permissions.xml",
        "data/ia_approval_mail.xml",
        "views/res_config_settings_views.xml",
        "views/operations_adjustment_reason.xml",
        "views/stock_quant_views.xml",
        "views/account_move.xml",
        "wizards/stock_inventory_adjustment_name.xml",
    ],
    "installable": True,
    "active": False,
}
