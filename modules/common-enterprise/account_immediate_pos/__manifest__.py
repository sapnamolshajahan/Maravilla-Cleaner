# -*- coding: utf-8 -*-
{
    "name": "Account Immediate Point of Sale",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "description": """Account Immediate Functionality for Point of Sale.
        This adds functionality to handle stock accounting correctly for POS transactions.
    
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
        "account_reports",
        'account_immediate',
        "point_of_sale"
    ],
    "data": [
        "wizards/account_stock_reconcile_dni.xml",
    ],
    "demo": [],
    "installable": True,
}
