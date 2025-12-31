# -*- coding: utf-8 -*-
{
    "name": "Odoo Backend Automatic Logout",
    "version": "1.0",
    "depends": [
        "web",
    ],
    "author": "OptimySME Ltd",
    "license": "Other proprietary",
    "website": "http://www.optimysme.co.nz",
    "category": "All",
    "description": "Allows you to automatically logout when you do not interact with odoo.",
    "data": [
        "data/ir_cron_data.xml",
        "views/view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoo_auto_logout/static/src/js/web.js",
        ],
    },
    "installable": True,
    "active": False,
}
