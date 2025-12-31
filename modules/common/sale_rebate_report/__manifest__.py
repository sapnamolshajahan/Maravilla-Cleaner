# -*- coding: utf-8 -*-
{
    "name": "Rebate Report",
    "version": "1.0",
    "category": "Reporting",
    "depends": [
        "base",
        "account",
        "sale",
        "sale_rebate_flag"
    ],
    "author": "OptimySME Limited",
    'website': 'http://www.optimysme.co.nz',
    "license": "Other proprietary",
    "description": """Rebate Report """,
    "data": [
            "wizard/rebate_report_view.xml",
            "wizard/csv_export_options_view.xml",
            "security/security.xml"],
    "installable": True,
    "active": False
}
