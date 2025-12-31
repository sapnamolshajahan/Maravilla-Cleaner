# -*- coding: utf-8 -*-
{
    'name': "Product Document",
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'author': 'OptimySME Limited',
    'website': 'https://optimysme.co.nz',
    'depends': ['stock', 'product', 'documents'],
    'data': [
        'security/security.xml',
        'views/product_docs_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
    'license': 'Other proprietary',
}
