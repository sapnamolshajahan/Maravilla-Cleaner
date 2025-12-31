# -*- coding: utf-8 -*-
{
    "name": "Optimysme Mail Templates Management",
    "version": "1.0",
    "category": "Mail",
    "depends": [
        "base",
        "mail",
        "mass_mailing",
        "mail_enterprise",
    ],
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "description": """
    For handling multiple emails with the same design.
    You can specify separate models with HTML design bodies, then reference those bodies from mail.template objects.
    You don't need to keep this HTML design in mail.templates - that simplifies management of content.
    
    Also adding unique IDs for each mail template that allows to reference email template from within the code.
    """,
    "data": [
        'security/mail_template_design_security.xml',
        'views/mail_template_design_view.xml',
        'views/mail_template_view.xml',
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "license": "Other proprietary"
}
