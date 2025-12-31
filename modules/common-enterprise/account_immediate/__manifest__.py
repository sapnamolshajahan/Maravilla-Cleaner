# -*- coding: utf-8 -*-
{
    "name": "Account Immediate",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "description": """Account Immediate Functionality.
        This adds functionality to handle stock accounting correctly.
    
""",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "depends": [
        "base",
        "sale",
        "stock_account",
        "purchase",
        "account",
        "queue_job",
        "queue_job_channels",
        "queue_job_notifications",
        "account_reports"
    ],
    "data": [
        "reports/stock_reconciliation_report.xml",
        "views/menus.xml",
        "views/company.xml",
        "views/product_category.xml",
        "views/res_config_settings.xml",
        "security/security.xml",
        "wizards/account_stock_reconcile_dni.xml",
        "wizards/account_stock_reconcile_rni.xml",
        "wizards/account_stock_reconcile_other.xml",
        "data/initial_setup.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'account_immediate/static/src/**/*',
        ],
    },
    "demo": [],
    "installable": True,
}
