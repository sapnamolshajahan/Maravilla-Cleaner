# -*- coding: utf-8 -*-
{
    "name": "Web Actions Multi",
    "summary": "Enables triggering of more than one action on ActionManager",
    "category": "Web",
    "author": "OptimySME Limited",
    "website": "https://www.optimysme.co.nz",
    "version": "1.0",
    "depends": ["web"],
    "data": ["security/ir.model.access.csv"],
    "assets": {
        "web.assets_backend": [
            "web_ir_actions_act_multi/static/src/**/*.esm.js",
        ],
    },
    "installable": True,
    "license": "Other proprietary",
}
