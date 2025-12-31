# -*- coding: utf-8 -*-
{
    "name": "Global View Changes",
    "version": "1.0",
    "depends": [
        "base",
    ],
    "author": "Solnet Solutions Ltd",
    "website": "http://www.solnetsolutions.co.nz",
    "category": "web",
    "description": """Makes view changes system-wide
    
    To disable the create and edit option as well as the open button on Many2xx widgets add this to the system
    parameters:
    views_global_changes.disable_m2o_create_edit : True
    
    Should you want to enable the create functionality for a select few fields, use {'allow_create': True}
    in the options attribute.
    """,
    "assets": {
        "web.assets_backend": [
            "views_global_changes/static/src/css/*",
        ],
    },
    "installable": True,
    "active": False,
}
