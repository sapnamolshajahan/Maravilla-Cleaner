# -*- coding: utf-8 -*-
{
    "name": "Sales Order Reports",
    "version": "1.0",
    "category": "Reporting",
    "depends": [
        "account",
        "base_generic_changes",
        "sale",
        "sale_stock",
        "jasperreports_viaduct",
    ],
    "author": "OptimySME Limited",
    'website': 'https://www.optimysme.co.nz',
    "license": "Other proprietary",
    "description": """ Generic Sale Order/Quotation Report""",
    "data": [
        "data/mail-template.xml",
        "reports/reports.xml",
        "views/config.xml",
        "views/sale_order.xml",
    ],
    "installable": True,
}
