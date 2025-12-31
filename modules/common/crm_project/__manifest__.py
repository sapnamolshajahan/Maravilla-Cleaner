# -*- coding: utf-8 -*-
{
    "name": "CRM Project",
    "version": "1.0",
    "depends": [
        "crm",
        "project",
        "hr",
        "account",
        "hr_timesheet",
        "sale",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "category": "CRM",
    "description": "used for a business that uses projects. This module creates the project from the opportunity and allows time to"
                   "be recorded against the opportunity using the project analytic account. ",
    "data": [
        "views/project.xml",
        "views/crm_lead.xml",
        "views/res_config_settings.xml"
    ],
    "installable": True,
    "active": False
}
