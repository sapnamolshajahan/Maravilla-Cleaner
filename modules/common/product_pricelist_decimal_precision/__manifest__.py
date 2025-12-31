# -*- coding: utf-8 -*-
{
    "name": "Product Pricelist Decimal Precision",
    "version": "1.0",
    "category": "Product",
    "depends": [
        "account",
        "base_generic_changes",  # Precision definitions
        "stock",
        "sale",
        "purchase",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """
        Sets the decimal precision for Stock Moves, Products, Price Lists, and Purchase Order lines to the 'Purchase Price' 
        Decimal Accuracy setting, which is 3 digits by default.
""",
    "data": [
        "views/product.xml",
    ],
    "installable": True,
    "active": False,
}
