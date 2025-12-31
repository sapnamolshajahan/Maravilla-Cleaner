# -*- coding: utf-8 -*-
{
    "name": "Odoo REST API",
    "version": "1.0",
    "category": "API",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "summary": "Odoo REST API",
    "description": """ RESTful API For Odoo. With use of this module user can enable REST API endpoint for any model.""",
    "depends": ["web"],
    "data": [
        "data/ir_config_param.xml",
        "views/ir_model.xml",
        "views/access_token_view.xml",
        "views/res_users.xml",
        "views/res_company.xml",
        "wizard/add_mapping_name_view.xml",
        "wizard/add_post_ref_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
}
