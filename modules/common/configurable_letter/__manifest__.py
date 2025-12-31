# -*- coding: utf-8 -*-
{
    "name": "Configurable Letters",
    "version": "1.0",
    "category": "General",
    "depends": [
        "mail",
        "base",
    ],
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "description": """
Letter Template
========================

* wizards
* basic functionality
""",
    "data": [
        "security/ir.model.access.csv",
        "security/letter_template_report_wizard_security.xml",
        "wizard/letter_template_report_view.xml",
        "views/letter_template_view.xml",
        "reports/generic_letter_to_contact_report.xml",
        "data/generic_letter_to_contact_email.xml",
        "data/generic_template.xml",
        "views/res_partner.xml",
        "views/res_config_settings.xml",
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "license": "Other proprietary"
}
