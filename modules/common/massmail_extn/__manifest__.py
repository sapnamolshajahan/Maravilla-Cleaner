# -*- coding: utf-8 -*-
{
    'name': 'MassMail Extension',
    'version': '1.0',
    'depends': ['mass_mailing'],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    'category': 'POS',
    'description': 'Mass Mail - add ability to build lists based on selection logic.',
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/mass_mailing.xml',
        'wizard/massmail.xml',
    ],
    'update_xml': [],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}
