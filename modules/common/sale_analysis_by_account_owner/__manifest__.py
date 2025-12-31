# -*- coding: utf-8 -*-
{
    "name": "Sale Analysis Report (by Account Owner)",
    "version": "11.0",
    "category": "Reporting",
    "depends": [
        "base",
        "account",
        "sale",
        "account_generic_changes",
        "queue_job",
        "queue_job_channels"
        ],
    'external_dependencies': {
        'python': ['pandas']},
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "description": "Sale Analysis Report",
    'data': [
        "views/sale_analysis_view.xml",
        "security/security.xml",
        "views/res_partner_views.xml"
        ],
    "installable": True,
    "active": False
    }
