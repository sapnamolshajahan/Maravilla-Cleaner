# -*- coding: utf-8 -*-
{
    "name": "Hazardous Substances",
    "version": "1.0",
    "category": "Generic Modules/Human Resources",
    "description": """
    Hazardous substances register for Health & Safety
    """,
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "depends": [
        "hr_hazard",
        "product",
        "stock",
        "sale_stock",
        "jasperreports_viaduct",
        "base_generic_changes",  # "Accounting" decimal-precision
    ],
    "data": [
        "views/product.xml",
        "report/reports.xml",
        "security/security.xml"
    ],
    "installable": True,
    "active": False,
}
