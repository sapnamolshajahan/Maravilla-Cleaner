# -*- coding: utf-8 -*-

{
    "name": "Purchases Alternate Shipping Address",
    "version": "19.0.1.0.0",
    "category": "Purchasing",
    "depends": [
        "purchase",
        "purchase_order_reports",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": "Add another Shipping Address for Purchase Orders.",
    "data": [
        "views/purchase.xml",
        "views/res_company_view.xml",
        "views/res_config_settings.xml"
    ],
    "post_load": "register_alt_address_helper",
    "installable": True,
    "active": False,
}
