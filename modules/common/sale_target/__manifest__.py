# -*- coding: utf-8 -*-
{
    "name": "Sales targets",
    "version": "1.0",
    "category": "Sales",
    "depends": [
        "sale",
        "base",
        "crm",
        "account"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "description": "Create sale targets by salesperson and reporting",
    "data": [
        "views/sale_target.xml",
        "views/res_config_settings_views.xml",
        "reports/sale_target_report_views.xml",
        "security/sale_quote.xml"
    ],
    "installable": True,
    "active": False,
}
