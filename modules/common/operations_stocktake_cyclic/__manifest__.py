# -*- coding: utf-8 -*-
{
    "name": "Operations - Stocktake Cyclic",
    "version": "1.0",
    "depends": [
        "stock",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "category": "Inventory Control",
    "description": """
        Provides stock take functionality for large businesses.
    """,
    "data": [
        "security/ir.model.access.csv",
        "datas/groups.xml",
        "datas/product_cyclic_count_cron.xml",
        "views/product_cyclic_count.xml",
        "views/product_template.xml",
        "views/stock_quant.xml",
    ],
    "installable": True,
    "active": False,
}
