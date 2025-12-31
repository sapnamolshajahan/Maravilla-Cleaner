# -*- coding: utf-8 -*-
{
    "name": "Base Generic Changes",
    "version": "19.0.1.0",
    "depends": [
        "mail",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.nz",
    "category": "Other",
    "data": [
        "security/groups.xml",
        "data/ir-config-parameter.xml",
        "data/mail-server.xml",
        "data/precisions.xml",
        "data/res-lang.xml",
        "views/menus.xml",  # Place before other views
        "views/company.xml",
        "views/country.xml",
        "views/currency.xml",
        "views/res_partner.xml",
        "wizards/base_module_uninstall_view.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
}
