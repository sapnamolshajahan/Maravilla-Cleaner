# -*- coding: utf-8 -*-
{
    "name": "Advance Flooring Sale",
    "version": "19.0.1.0.0",
    "category": "Sale",
    "description": """""",
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://www.optimysme.co.nz",
    "depends": [
        "web",
        "sale_management",
        "sale_generic_changes",
    ],
    "data": [
        'security/ir.model.access.csv',
        'report/sale_order.xml',
        'report/packing_slip.xml',
        'report/tax_invoice.xml',
        'report/report.xml',
        "views/sale_order.xml",
        "views/stock_picking.xml",
        "views/product_hold.xml",
    ],
    "installable": True,
    "active": False,
}
