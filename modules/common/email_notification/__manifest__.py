# -*- coding: utf-8 -*-
{
    "name": "Send Email Notifications for Queue Jobs",
    "version": "19.0.1.0.0",
    "category": "Social Network",
    "depends": ["base", "base_generic_changes", "queue_job"],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """Send email notifications""",
    "data": [
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'views/res_company_view.xml',
    ],
    "test": [],
    "installable": True,
    "active": False,
}
