# -*- coding: utf-8 -*-
{
    "name": "HR Contractor",
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
        "views/induction_questions.xml",
        "views/visitor_type.xml",
        "views/visitor_log.xml"
    ],
    "installable": True,
    "active": False,
}
