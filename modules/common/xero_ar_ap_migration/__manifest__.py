# -*- coding: utf-8 -*-
{
    'name': 'Import AR or AP from Xero ATB',
    'version': '19.0.1.0',
    'author': 'OptimySME Limited',
    "license": "Other proprietary",
    'category': 'Accounting',
    'description': """
            Script to process a standard AR or AP detailed trial balance form Xero
    """,
    'website': 'http://www.optimysme.co.nz',
    'images': [],
    'depends': ['base', 'account'],
    'data': [
        "wizards/xero_import.xml",
        "security/security.xml"
    ],
    'qweb': [],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
