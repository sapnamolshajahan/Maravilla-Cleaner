# -*- coding: utf-8 -*-
{
    "name": "Purchase to Sale Order Cost Update",
    "version": "1.0",
    "depends": [
        "purchase",
        "sale_margin",
        "sale_stock",
        "sale_purchase"
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "category": "Inventory",
    "description": "Cost and Purchase Order number from PO line updated to linked SO line",
    "data": [
        "views/sale_order_line_view.xml",
    ],
    "installable": True,
    "active": False,
}
