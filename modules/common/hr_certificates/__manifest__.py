# -*- coding: utf-8 -*-
{
    "name": "HR Certificates",
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
        'data/mail_template.xml',
        'data/ir_cron_data.xml',
        "views/hr_certificates.xml",
        "views/certificate_type.xml",
        "views/hr_employee.xml"
    ],
    "installable": True,
    "active": False,
}
