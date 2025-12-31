# -*- coding: utf-8 -*-
{
    "name": "Basic Invoice Report",
    "version": "19.0.1.0.0",
    "category": "Reporting",
    "depends": [
        "account_generic_changes",
        "product",
        "jasperreports_viaduct"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": """
Generic Invoice Print
=====================

* designed for Service Business
* no Sale Order or Picking
""",
    "data": [
        "reports/reports.xml",
        "views/invoice.xml",
    ],
    'external_dependencies': {'python': ['bs4']},
    "installable": True,
}
