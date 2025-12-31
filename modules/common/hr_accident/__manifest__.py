# -*- coding: utf-8 -*-

{
    "name": "Incident Tracking",
    "version": "19.0.1.0.0",
    "category": "Generic Modules/Human Resources",
    "description": "Tracking Workplace Incidents and Accidents.",
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "depends": [
        "hr",
        "jasperreports_viaduct",
        "hr_hazard"
    ],
    "data" : [
        "security/ir.model.access.csv",
        "views/hr_accident_view.xml",
        "data/hr_accident_sequence.xml",
        "views/hr_hazard_view.xml",
        "report/reports.xml",
    ],
    "installable": True,
    "active": False,
}
