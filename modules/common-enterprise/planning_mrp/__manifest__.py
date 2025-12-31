# -*- coding: utf-8 -*-
{
    "name": "Planning Workorder Link",
    "version": "1.0",
    "category": "Human Resources/Planning",
    "description": """
    Links planning and workorders. 
    """,
    "author": "Optimysme Limited",
    "depends": [
        "base",
        "account",
        "planning",
        "mrp",
    ],
    "data": [
        "views/planning_role.xml",
        "views/planning_slot.xml",

    ],
    "installable": True,
    "active": False,
}
