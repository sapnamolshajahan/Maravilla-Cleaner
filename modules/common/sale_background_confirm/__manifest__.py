# -*- coding: utf-8 -*-
{
    "name": "Sale Order Background Confirm",
    "version": "1.0",
    "category": "Sales",
    "depends": [
        "sale",
        "sale_stock",
        "queue_job",
        "queue_job_channels",
        "res_partner_credit_limit",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "description": """
        Confirms Sale Orders in a background task. 
    """,
    "data": [
        "views/sale_order_view.xml",
        "views/res_config_settings_views.xml",
        ],
    "installable": True,
    "active": False,
}
