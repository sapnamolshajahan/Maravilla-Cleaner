# -*- coding: utf-8 -*-
{
    "name": "Simple Multi-Location Stock",
    "version": "19.0.1.0.0",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Stock",
    "description": """
This is a simple implementation of multiple stock locations, using warehouse bins.
""",
    "depends": [
        "base",
        "base_generic_changes",  # "Accounting" decimal-precision
        "sale",
        "stock",
        "product"
    ],
    "data": [
        "security/stock_multibin_security.xml",
        "security/ir.model.access.csv",
        "views/company.xml",
        "views/product_view.xml",
        "views/stock_warehouse_bin.xml",
        "views/stock_view.xml",
    ],
    "active": False,
    "installable": True,
}
