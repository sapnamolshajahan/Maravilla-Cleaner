# -*- coding: utf-8 -*-
{
    "name": "Health and Safety Module",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "description": """""",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "depends": [
        "hr",
        "hr_hazard",
        "mail",
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/cron_job_data.xml',
        "views/health_safety_policy.xml"
    ],
    "installable": True,
    "active": False,
}
