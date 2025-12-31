# -*- coding: utf-8 -*-
{
    "name": "Product Multi-Company",
    "version": "19.0.1.0",
    "category": "Stock",
    "depends": ["product",'stock'],
    "author": "Optimysme Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "description": """
        Various changes that are required for products in a multi-company situation
    """,
    "data": [
        "data/product-template.xml",
        "security/security.xml",
        "views/product_category.xml"
    ],
    'pre_init_hook': 'pre_init_hook',
    "installable": True,
    "active": False,
}
