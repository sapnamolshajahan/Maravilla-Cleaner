# -*- coding: utf-8 -*-
{
    "name": "Sale Order Generic Changes",
    "version": "1.0",
    "category": "Sales",
    "depends": [
        "base_generic_changes",
        "sale_crm",  # sale.tag_ids
        "sale_margin",
        "sale_stock",
        "sales_team",
        "account",
        "stock",
        "purchase",
        "operations_generic_changes",
        'product',
        "base",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "description": """Sale order fields rearrangement and new field - margin %. Adds contact to SO""",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizard/sort_lines.xml",
        "views/res_config_settings_views.xml",
        "views/invoice.xml",
        "views/menus.xml",
        "views/picking.xml",
        "views/res_partner.xml",
        "views/product_pricelist_item_view.xml",
        "views/sale_order.xml",
        "data/sale_order.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'sale_generic_changes/static/src/js/form_renderer.js',
        ],
    },
    "installable": True,
    "active": False,
}
