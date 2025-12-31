# -*- coding: utf-8 -*-
{
    "name": "Project to Purchase",
    "version": "1.0",
    "depends": [
        "base",
        "purchase",
        "stock",
        'product',
        'project'
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "category": "Project",
    "description": """
    In the Project settings page  this module add a  new button 'New PO' which create a new RFQ. The New RFQ is linked \
    to the Project and has  lines  default to an Analytical Distribution that is the Project.
    """,
    "data": [
        "views/purchase_order.xml",
        "views/project.xml",
    ],
    "installable": True
}
