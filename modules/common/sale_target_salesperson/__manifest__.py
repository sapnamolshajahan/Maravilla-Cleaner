# -*- coding: utf-8 -*-
{
    'name': 'Sale Budget',
    'version': '1.0',
    'depends': ['base', 'sale', 'sales_team', 'crm'],
    "author": "OptimySME Limited",
    'website': 'http://www.optimysme.co.nz',
    'category': 'Sales',
    'description': ' Sales Budget',
    "license": "Other proprietary",
    'data': [
        "views/sales_budget_view.xml",
        "security/ir.model.access.csv",
        "reports/sale_budget_report_views.xml",
        "reports/sale_budget_report_v2.xml",
        "security/security.xml",
        "data/cron.xml"
    ],
    'update_xml': [],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}
