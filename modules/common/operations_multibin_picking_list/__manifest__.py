# -*- coding: utf-8 -*-
{
    "name": "Operation Multi-Bin Picking List",
    "version": "1.0",
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "license": "Other proprietary",
    "category": "Stock",
    "description": """
      Bin For Picking List Reports.
""",
    "depends": [
        "operations_multibin",
        "operations_picking_list_reports",
        "jasperreports_viaduct",
        "operations_generic_changes"
    ],
    "data": [
        "reports/reports.xml"
    ],
    "active": False,
    "installable": True,
}
