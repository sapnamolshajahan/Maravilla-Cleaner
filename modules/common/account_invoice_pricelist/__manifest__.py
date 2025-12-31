# -*- coding: utf-8 -*-
{
    "name": "Price List Lookups on Invoices",
    "version": "1.0",
    "category": "Invoicing",
    "depends": [
        "account",
        "product",
    ],
    "author": "OptimySME Limited",
    "license": "Other proprietary",
    "website": "https://optimysme.co.nz",
    "description": """
Associate Price Lists with Invoices, and allow it to be changed.

Note that prices on line items do not change, and are set to standard price. The module simply
applies discounts onto the line item.
""",
    "data": [
        "views/invoice.xml",
    ],
    "installable": True,
    "active": False
}
