# -*- coding: utf-8 -*-
{
    "name": "Hazard Tracking",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "description": """
        Hazards tracking module for Health & Safety
    """,
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.nz",
    "depends": [
        "hr",
        "jasperreports_viaduct",
    ],
    "data": [
        "data/hr_hazard_sequence.xml",
        "security/hr_hazard_security.xml",
        "security/ir.model.access.csv",
        "views/hr_hazard_view.xml",
        "report/reports.xml"
    ],
    "demo": [],
    "installable": True,
    "active": False,
}
