# -*- coding: utf-8 -*-
{
    "name": "Risk Tracking",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "description": """
        Risk tracking module for Health & Safety
    """,
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.nz",
    "depends": [
        "hr",
        "jasperreports_viaduct",
        "hr_accident"
    ],
    "data": [
        "data/hr_risk_sequence.xml",
        "security/ir.model.access.csv",
        "views/hr_accident.xml",
        "views/hr_risk_view.xml",
        "report/reports.xml"
    ],
    "demo": [],
    "installable": True,
    "active": False,
}
