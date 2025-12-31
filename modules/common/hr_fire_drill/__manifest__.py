# -*- coding: utf-8 -*-
{
    "name": "HR Fire Drill",
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
        'data/mail_templates.xml',
        'data/fire_drills_sequence.xml',
        'data/fire_drill_cron.xml',
        "views/fire_drills.xml",
    ],
    "installable": True,
    "active": False,
}
