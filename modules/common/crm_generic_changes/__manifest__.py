# -*- coding: utf-8 -*-
{
    "name": "CRM Extensions",
    "version": "1.0",
    "depends": [
        "crm",
        "mail",
        "sales_team",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "category": "CRM",
    "description": "Provides some generic changes to the CRM module",
    "data": [
        "views/crm_lead.xml",
        "views/mail_activity.xml",
        "views/partner.xml",
        "wizards/crm_lead_to_opportunity.xml",
        "wizards/lead_new_contact.xml",
    ],
    "installable": True,
    "active": False
}
